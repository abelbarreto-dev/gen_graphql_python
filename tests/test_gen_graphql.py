import ast
import unittest

from gen_graphql import GenGraphQL


class GenGraphQLTests(unittest.TestCase):
    def setUp(self) -> None:
        self.generator = GenGraphQL()

    def test_extract_enums(self) -> None:
        code = """
from enum import Enum

class Status(Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
"""
        tree = ast.parse(code)

        enums = self.generator.extract_enums(tree)

        self.assertEqual(enums, {"Status": ["ACTIVE", "INACTIVE"]})

    def test_extract_resolvers_with_query_and_mutation(self) -> None:
        code = """
from typing import Annotated
from graphql import query, mutation, Arg

@query
async def get_user(id: Annotated[int, Arg()]):
    pass

@mutation
async def create_user(name: Annotated[str, Arg()]):
    pass
"""

        queries, mutations = self.generator.extract_resolvers(code)

        self.assertIn("getUser(id: Int!): Void", queries)
        self.assertIn("createUser(name: String!): Void", mutations)

    def test_convert_type_supports_common_python_types(self) -> None:
        self.assertEqual(self.generator.py_to_graphql("str"), "String")
        self.assertEqual(self.generator.py_to_graphql("int"), "Int")
        self.assertEqual(self.generator.py_to_graphql("bool"), "Boolean")
        self.assertEqual(self.generator.py_to_graphql("UUID"), "ID")
        self.assertEqual(self.generator.py_to_graphql("date"), "Date")


if __name__ == "__main__":
    unittest.main()
