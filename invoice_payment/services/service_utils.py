import json
from typing import Union

from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction

from invoice_payment.models import Invoice
from invoice_payment.validation.invoice import InvoiceModelValidation
from django.forms.models import model_to_dict


def _check_authentication(function):
    def wrapper(self, *args, **kwargs):
        if type(self.user) is AnonymousUser or not self.user.id:
            return {
                "success": False,
                "message": "Authentication required",
                "detail": "PermissionDenied",
            }
        else:
            result = function(self, *args, **kwargs)
            return result
    return wrapper


def _model_representation(model):
    uuid_string = str(model.id)
    dict_representation = model_to_dict(model)
    dict_representation["id"], dict_representation["uuid"] = (str(uuid_string), str(uuid_string))
    return dict_representation


def _output_exception(model_name, method, exception):
    return {
        "success": False,
        "message": f"Failed to {method} {model_name}",
        "detail": str(exception),
        "data": "",
    }


def _output_result_success(dict_representation):
    return {
        "success": True,
        "message": "Ok",
        "detail": "",
        "data": json.loads(json.dumps(dict_representation, cls=DjangoJSONEncoder)),
    }


def _build_delete_instance_payload():
    return {
        "success": True,
        "message": "Ok",
        "detail": "",
    }


def _get_generic_type(generic_type: Union[str, ContentType]):
    if isinstance(generic_type, ContentType):
        return generic_type
    elif isinstance(generic_type, str):
        return ContentType.objects.get(model=generic_type.lower())
    else:
        return ContentType.objects.get(model=str(generic_type).lower())