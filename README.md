# Gen GraphQL Python

Gerador de tipos, inputs e operações GraphQL a partir de modelos Python, enums e resolvers definidos em arquivos de projeto.

## O que este projeto faz

Este utilitário lê arquivos Python do seu projeto e gera um schema GraphQL em formato textual. Ele suporta:

- classes BaseModel para gerar inputs e tipos GraphQL;
- enums Python para gerar enums GraphQL;
- funções assíncronas decoradas com query ou mutation para gerar operações GraphQL;
- argumentos de função com assinatura usando Annotated[Type, Arg()] para mapear parâmetros de entrada.

## Como usar

1. Coloque o módulo do GraphQL no projeto em uma pasta de utilidades ou de núcleo, dependendo da arquitetura usada, por exemplo:
   - utils/
   - core/
   - app/core/

2. Importe as funções e a classe auxiliares do arquivo graphql.py:

```python
from typing import Annotated
from graphql import query, mutation, Arg
```

3. Defina seus modelos, enums e resolvers em arquivos com nomes que o gerador reconhece:
   - \*Input.py
   - \*DTO.py
   - \*\_resolver.py

Exemplo de resolver:

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

Exemplo de input/DTO:

```python
from pydantic import BaseModel

class UserInput(BaseModel):
    name: str
    age: int
```

O argumento que não possuir essa configuração com Annotated, é ignorado ao gerar a
query ou mutation.

4. Crie o arquivo de configuração na raiz do projeto chamado gen.graphql.json.

O arquivo inicial é gerado automaticamente na primeira execução, mas precisa ser ajustado com os caminhos corretos do projeto.

Exemplo de conteúdo:

```json
{
  "resolvers": "./app/resolvers",
  "inputs": "./app/inputs",
  "enums": "./app/enums",
  "dtos": "./app/dtos",
  "schema_file": "./schema.graphql"
}
```

5. Execute o script:

```bash
python gen_graphql.py
```

Na primeira execução, o arquivo JSON é criado e o programa pede que você o configure. Na segunda execução, com o arquivo devidamente preenchido, ele gera o schema GraphQL.

### Sugestão simples com Yarn/Node

Se você quiser apenas um atalho para rodar o gerador em comandos do projeto, pode adicionar um script básico no package.json:

```json
{
  "scripts": {
    "graphql:gen": "python gen.graphql.py"
  }
}
```

Assim, o comando fica:

```bash
yarn graphql:gen
```

## Regras de descoberta de arquivos

O gerador procura arquivos com os seguintes padrões:

- \*Input.py
- \*DTO.py
- \*\_resolver.py

Além disso, ele também lê arquivos de enums com o padrão:

- \*\_enum.py

## Estrutura esperada para os resolvers

Os resolvers devem:

- usar @query ou @mutation como decorador de função;
- usar a assinatura com Annotated[Type, Arg()] nos argumentos;
- retornar um tipo que possa ser mapeado para GraphQL.

## Observações técnicas relevantes

- O gerador usa AST para inspecionar os arquivos Python, então ele depende da sintaxe esperada pelo código.
- Os tipos Python mais comuns são convertidos para tipos GraphQL, como:
  - str -> String
  - int -> Int
  - float -> Float
  - bool -> Boolean
  - UUID -> ID
  - date/datetime -> Date/DateTime
- O arquivo gerado é salvo no caminho informado em schema_file.

## Testes

Foram incluídos testes unitários básicos para validar a lógica principal do gerador, incluindo:

- extração de enums;
- identificação de query e mutation;
- mapeamento de tipos comuns.

Execute os testes com:

```bash
python -m unittest discover -s tests
```

## Próximos passos

- ajustar os caminhos no arquivo gen.graphql.json para o seu projeto;
- organizar os arquivos de inputs, DTOs, enums e resolvers seguindo a convenção esperada;
- revisar o schema gerado e adaptar o código conforme a estrutura da sua API.

Leia também a versão em inglês: [README_EN.md](README_EN.md).

## Licença

Este projeto é licenciado sob a licença MIT. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.
