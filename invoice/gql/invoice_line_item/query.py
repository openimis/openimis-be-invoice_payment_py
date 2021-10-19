import graphene
from django.contrib.auth.models import AnonymousUser
from django.db.models import Q
from policy.apps import PolicyConfig

from core.schema import OrderedDjangoFilterConnectionField
from core.utils import append_validity_filter
from invoice.apps import InvoiceConfig
from invoice.gql.gql_types import InvoiceLineItemGQLType
from invoice.models import InvoiceLineItem
import graphene_django_optimizer as gql_optimizer


class InvoiceLineItemQueryMixin:
    invoice_line_item = OrderedDjangoFilterConnectionField(
        InvoiceLineItemGQLType,
        orderBy=graphene.List(of_type=graphene.String),
        dateValidFrom__Gte=graphene.DateTime(),
        dateValidTo__Lte=graphene.DateTime(),
        applyDefaultValidityFilter=graphene.Boolean(),
    )

    def resolve_invoice_line_item(self, info, **kwargs):
        filters = []
        filters += append_validity_filter(**kwargs)
        InvoiceLineItemQueryMixin._check_invoice_permissions(info.context.user)
        return gql_optimizer.query(InvoiceLineItem.objects.filter(*filters).all(), info)

    @staticmethod
    def _check_invoice_permissions(user):
        if type(user) is AnonymousUser or not user.id or not user.has_perms(
                InvoiceConfig.gql_invoice_search_perms):
            raise PermissionError("Unauthorized")


