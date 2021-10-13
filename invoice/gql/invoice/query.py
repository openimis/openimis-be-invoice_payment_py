import graphene
from django.contrib.auth.models import AnonymousUser
from policy.apps import PolicyConfig

from core.schema import OrderedDjangoFilterConnectionField
from core.utils import append_validity_filter
from invoice.gql.gql_types import InvoiceGQLType
from invoice.models import Invoice
import graphene_django_optimizer as gql_optimizer


class InvoiceQueryMixin:
    invoice = OrderedDjangoFilterConnectionField(
        InvoiceGQLType,
        orderBy=graphene.List(of_type=graphene.String),
        dateValidFrom__Gte=graphene.DateTime(),
        dateValidTo__Lte=graphene.DateTime(),
        applyDefaultValidityFilter=graphene.Boolean(),
    )

    def resolve_invoice(self, info, **kwargs):
        filters = []
        filters += append_validity_filter(**kwargs)
        InvoiceQueryMixin.__check_invoice_permissions(info.context.user)
        return gql_optimizer.query(Invoice.objects.filter(*filters).all(), info)

    @staticmethod
    def __check_invoice_permissions(user):
        # TODO: What permissions should we use?
        if type(user) is AnonymousUser or not user.id or not user.has_perms(
                PolicyConfig.gql_mutation_create_policies_perms):
            raise PermissionError("Unauthorized")


