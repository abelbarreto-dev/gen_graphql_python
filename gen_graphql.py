import ast
import json
from os import listdir
from os.path import isfile
from re import compile

from pydantic import BaseModel

standard_file = """{
  "resolvers": "<path-to-resolvers>",
  "inputs": "<path-to-inputs>",
  "enums": "<path-to-enums-files>",
  "dtos": "<path-to-dtos-files>",
  "schema_file": "<path-to-schema-file>"
}"""

json_file = "./gen.graphql.json"


class Paths(BaseModel):
    resolvers: str
    inputs: str
    enums: str
    dtos: str
    schema_file: str


class GenGraphQL:
    def __init__(self):
        pass

    def main(self) -> None:
        setup = self.setup()

        if not setup:
            return

        paths = self.get_paths()

        rg = compile(r"^[A-Z][a-zA-Z]+[a-z]\.py$")

        inputs = listdir(paths.inputs)
        inputs = [i for i in inputs if rg.match(i) is not None]
        graphql = "scalar Date\nscalar DateTime\n\n"

        en_fl = compile(r"^[a-z]+_enum.py$")

        enums = listdir(paths.enums)
        enums = [i for i in enums if en_fl.match(i) is not None]

        for enum in enums:
            with open(f"{paths.enums}/{enum}", "r", encoding="utf-8") as file:
                code = file.read()

                tree = ast.parse(code)

                enumerates = self.extract_enums(tree)

                data = self.generate_graphql_enums(enumerates)

                graphql += f"{data}\n\n"

        for input in inputs:
            with open(f"{paths.inputs}/{input}", "r", encoding="utf-8") as file:
                code = file.read()

            data = self.extract_graphql_types(code)
            graphql += f"{data}\n\n"

        tp_dtos = compile(r"^[A-Z][a-zA-Z]+[a-z]DTO.py")
        dtos = listdir(paths.dtos)
        dtos = [i for i in dtos if tp_dtos.match(i) is not None]

        for dto in dtos:
            with open(f"{paths.dtos}/{dto}", "r", encoding="utf-8") as file:
                code = file.read()

            data = self.extract_graphql_types(code, True)
            graphql += f"{data}\n\n"

        resolv = compile("^[a-z][a-z_]+[a-z]_resolver.py$")
        resolvers = listdir(paths.resolvers)
        resolvers = [i for i in resolvers if resolv.match(i) is not None]

        queries = mutations = ""

        for resolver in resolvers:
            with open(f"{paths.resolvers}/{resolver}", "r", encoding="utf-8") as file:
                code = file.read()

            q, m = self.extract_resolvers(code)
            queries += q
            mutations += m

        queries = self.format_operation("Query", queries)
        mutations = self.format_operation("Mutation", mutations)

        graphql += f"{queries}\n\n{mutations}\n"

        with open(paths.schema_file, "w", encoding="utf-8") as writer:
            writer.write(graphql)

    def setup(self) -> bool:
        py_dict = json.loads(standard_file)

        if not isfile(json_file):
            with open(json_file, "w", encoding="utf-8") as file:
                file.write(standard_file)
            print("please, configure the file 'gen.graphql.json' on the root!")
            print("need to be valid directories or python package")
            return False

        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        is_keys = data.keys() == py_dict.keys()

        if not is_keys:
            with open(json_file, "w", encoding="utf-8") as file:
                file.write(standard_file)
            print("please, configure the file 'gen.graphql.json' on the root!")
            print("need to be valid directories or python package")
            return False

        return True

    def get_paths(self) -> Paths:
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        return Paths(**data)

    def extract_enums(self, tree: ast.Module):
        enums = {}

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                if not any(
                    isinstance(base, ast.Name) and base.id == "Enum"
                    for base in node.bases
                ):
                    continue

                enum_name = node.name
                values = []

                for item in node.body:
                    if isinstance(item, ast.Assign):
                        if isinstance(item.targets[0], ast.Name):
                            values.append(item.targets[0].id)

                enums[enum_name] = values

        return enums

    def generate_graphql_enums(self, enums: dict):
        output = []

        for name, values in enums.items():
            body = "\n".join(f"  {v}" for v in values)
            gql = f"enum {name} {{\n{body}\n}}"
            output.append(gql)

        return "\n\n".join(output)

    def extract_graphql_types(self, code: str, is_output: bool = False):
        tree = ast.parse(code)
        output = []

        status = "input" if not is_output else "type"

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                if not any(
                    isinstance(base, ast.Name) and base.id == "BaseModel"
                    for base in node.bases
                ):
                    continue

                fields = []

                for item in node.body:
                    if isinstance(item, ast.AnnAssign):
                        name = item.target.id
                        py_type = self.get_type(item.annotation)

                        gql_type, required = self.convert_type(py_type)

                        if required:
                            gql_type = f"{gql_type}!"

                        fields.append(f"  {name}: {gql_type}")

                gql = f"{status} {node.name} {{\n" + "\n".join(fields) + "\n}"
                output.append(gql)

        return "\n\n".join(output)

    def extract_resolvers(self, code: str):
        tree = ast.parse(code)

        queries = []
        mutations = []

        for node in tree.body:
            if isinstance(node, ast.AsyncFunctionDef):
                op_type = self.get_operation_type(node)

                if not op_type:
                    continue

                name = self.to_camel_case(node.name)
                args = self.extract_args(node)
                return_type = self.get_return_type(node)

                gql = f"{name}({', '.join(args)}): {return_type}"

                if op_type == "query":
                    queries.append(gql)
                else:
                    mutations.append(gql)

        return "\n".join(q for q in queries), "\n".join(m for m in mutations)

    def get_operation_type(self, func: ast.FunctionDef):
        for decorator in func.decorator_list:
            if isinstance(decorator, ast.Name):
                if decorator.id == "mutation":
                    return "mutation"
                if decorator.id == "query":
                    return "query"
        return None

    def to_camel_case(self, s: str) -> str:
        parts = s.split("_")
        return parts[0] + "".join(p.capitalize() for p in parts[1:])

    def extract_args(self, func: ast.FunctionDef):
        args = []

        for arg in func.args.args:
            name = arg.arg
            annotation = arg.annotation

            if not annotation:
                continue

            is_graphql_arg, py_type = self.is_arg(annotation)

            if not is_graphql_arg:
                continue

            gql_type, required = self.convert_type(py_type)

            if required:
                gql_type += "!"

            args.append(f"{name}: {gql_type}")

        return args

    def is_arg(self, annotation: ast.AST) -> tuple[bool, str]:
        if isinstance(annotation, ast.Subscript):
            if (
                isinstance(annotation.value, ast.Name)
                and annotation.value.id == "Annotated"
            ):
                # pega os elementos dentro do Annotated
                if isinstance(annotation.slice, ast.Tuple):
                    main_type = annotation.slice.elts[0]
                    metadata = annotation.slice.elts[1:]

                    for meta in metadata:
                        if (
                            isinstance(meta, ast.Call)
                            and getattr(meta.func, "id", "") == "Arg"
                        ):
                            return True, self.get_type(main_type)

        return False, self.get_type(annotation)

    def get_return_type(self, func: ast.FunctionDef):
        if not func.returns:
            return "Void"

        py_type = self.get_type(func.returns)
        gql_type, required = self.convert_type(py_type)

        if required:
            gql_type += "!"

        return gql_type

    def get_type(self, annotation):
        if isinstance(annotation, ast.Name):
            return annotation.id

        if isinstance(annotation, ast.Attribute):
            return f"{self.get_type(annotation.value)}.{annotation.attr}"

        if isinstance(annotation, ast.Subscript):
            base = self.get_type(annotation.value)

            if hasattr(annotation, "slice"):
                inner = self.get_type(annotation.slice)
            else:
                inner = self.get_type(annotation.slice.value)

            return f"{base}[{inner}]"

        if isinstance(annotation, ast.Tuple):
            return ", ".join(self.get_type(elt) for elt in annotation.elts)

        return "Unknown"

    def convert_type(self, py_type: str):
        if py_type.startswith("Optional["):
            inner = py_type[len("Optional[") : -1]
            gql_type, _ = self.convert_type(inner)
            return gql_type, False

        gql_type = self.py_to_graphql(py_type)
        return gql_type, True

    def py_to_graphql(self, key: str) -> str:
        return {
            "str": "String",
            "int": "Int",
            "float": "Float",
            "bool": "Boolean",
            "Decimal": "Float",
            "uuid.UUID": "ID",
            "UUID": "ID",
            "date": "Date",
            "datetime": "DateTime",
        }.get(key, key)

    def format_operation(self, operation: str, body: str) -> str:
        if not body.strip():
            return ""

        body = body.split("\n")
        body = [f"  {b}\n" for b in body]
        body = "".join(body)
        body = body[0:-1]

        return f"type {operation} {{\n{body}\n}}"


gen = GenGraphQL()
gen.main()
