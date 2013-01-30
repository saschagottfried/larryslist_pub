from jsonclient.backend import DBMessage
from larryslist.admin.apps.settings.models import CreateUserProc
from larryslist.lib.baseviews import GenericSuccessMessage
from larryslist.lib.formlib.formfields import BaseForm, StringField, EmailField


class FeederCreateForm(BaseForm):
    fields = [
        StringField("name", "Name")
        , EmailField("email", "Email")
        , StringField("pwd", "Password")
    ]

    @classmethod
    def on_success(cls, request, values):
        try:
            result = CreateUserProc(request, values)
        except DBMessage, e:
            result = {'success':False, 'errors':{}, 'values':values}
            if e.message == 'EMAIL_TAKEN':
                result['errors'] = {'email':"Email already taken"}
            else:
                result['message'] = e.message
            return result
        request.session.flash(GenericSuccessMessage("New user {name} ({email}) created".format(**values)), "generic_messages")
        return {'success':True, 'redirect':request.fwd_url("admin_settings_feeder_create")}