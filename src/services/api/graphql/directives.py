from ariadne import SchemaDirectiveVisitor, ObjectType
from . mutations import make_resolver

#mutation = ObjectType("Mutation")

class DataDirective(SchemaDirectiveVisitor):
    def visit_field_definition(self, field, object_type):
        name = f'{field.type}'
        # field.type contains the return value of the mutation; trim value
        # to produce canonical name
        name = name.replace('Result', '', 1)

        func = make_resolver(name)
        field.resolve = func
