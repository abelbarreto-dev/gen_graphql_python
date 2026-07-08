def mutation(func):
    func._gql_type = "mutation"
    return func


def query(func):
    func._gql_type = "query"
    return func


class Arg:
    pass
