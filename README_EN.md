# gen_graphql_python

Generator for GraphQL types, inputs, and operations from Python models, enums, and resolvers defined in your project files.

## What this project does

This utility reads Python files from your project and generates a GraphQL schema as text. It supports:

- BaseModel classes to generate GraphQL inputs and types;
- Python enums to generate GraphQL enums;
- asynchronous functions decorated with query or mutation to generate GraphQL operations;
- function arguments using the Annotated[Type, Arg()] signature to map input parameters.

## How to use

1. Place the GraphQL module in your project under a utilities or core folder, depending on your architecture, for example:
   - utils/
   - core/
   - app/core/

2. Import the helper functions and class from the graphql.py file:

```python
from typing import Annotated
from graphql import query, mutation, Arg
```

3. Define your models, enums, and resolvers in files that the generator recognizes:
   - \*Input.py
   - \*DTO.py
   - \*\_resolver.py

Example resolver:

```python
from typing import Annotated
from graphql import query, mutation, Arg

@query
async def get_user(id: Annotated[int, Arg()]) -> SomeType:
    return {"id": id}

@mutation
async def create_user(name: Annotated[str, Arg()]) -> SomeType:
    return {"name": name}
```

Example input/DTO:

```python
from pydantic import BaseModel

class UserInput(BaseModel):
    name: str
    age: int
```

The attributes those have not this setting using Annotated, it's intentionally missing to
generate a query or mutation.

4. Create the configuration file at the project root named gen.graphql.json.

The initial file is created automatically on the first run, but it must be adjusted with the correct project paths.

Example:

```json
{
  "resolvers": "./app/resolvers",
  "inputs": "./app/inputs",
  "enums": "./app/enums",
  "dtos": "./app/dtos",
  "schema_file": "./schema.graphql"
}
```

5. Run the script:

```bash
python gen_graphql.py
```

On the first execution, the JSON file is created and the program asks you to configure it. On the second execution, with the file properly filled in, it generates the GraphQL schema.

### Simple Yarn/Node shortcut

If you want a simple command shortcut for running the generator, you can add a basic script to package.json:

```json
{
  "scripts": {
    "graphql:gen": "python gen_graphql.py"
  }
}
```

Then you can run:

```bash
yarn graphql:gen
```

## File discovery rules

The generator searches for files matching these patterns:

- \*Input.py
- \*DTO.py
- \*\_resolver.py

It also reads enum files matching:

- \*\_enum.py

## Resolver structure

Resolvers should:

- use @query or @mutation as a function decorator;
- use the Annotated[Type, Arg()] signature for arguments;
- return a type that can be mapped to GraphQL.

## Relevant technical notes

- The generator uses AST to inspect Python files, so it depends on the expected syntax.
- Common Python types are converted to GraphQL types, such as:
  - str -> String
  - int -> Int
  - float -> Float
  - bool -> Boolean
  - UUID -> ID
  - date/datetime -> Date/DateTime
- The generated output is saved to the path specified in schema_file.

## Tests

Basic unit tests were added to validate the main generator logic, including:

- enum extraction;
- detection of query and mutation;
- mapping of common types.

Run the tests with:

```bash
python -m unittest discover -s tests
```

## Next steps

- adjust the paths in gen.graphql.json for your project;
- organize your inputs, DTOs, enums, and resolvers following the expected convention;
- review the generated schema and adapt the code according to your API structure.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for more details.
