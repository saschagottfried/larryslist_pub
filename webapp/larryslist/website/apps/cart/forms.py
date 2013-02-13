import formencode
from larryslist.lib.baseviews import GenericErrorMessage
from larryslist.lib.formlib.formfields import BaseForm, ConfigChoiceField, REQUIRED, EmailField, PasswordField, PlainHeadingField, StringField, CheckboxField, CheckboxPostField, CombinedField, HtmlAttrs
from larryslist.website.apps.auth import LoginForm, SignupForm
from larryslist.website.apps.auth.models import RefreshUserProfileProc
from larryslist.website.apps.cart.models import PurchaseCreditProc, SpendCreditProc


class PaymentOptionField(ConfigChoiceField):
    template = "larryslist:website/templates/cart/ajax/optionfield.html"

    def isSelected(self, option, value, request):
        if not value: value = request.session.get('PREFERRED_OPTION')
        return option.getKey(request) == value

class PaymentOptionsForm(BaseForm):
    fields = [PaymentOptionField("option", None, "PaymentOption", default_none = False)]
    action_label = "Buy your plan now"
    @classmethod
    def on_success(cls, request, values):
        request.session['PREFERRED_OPTION'] = values['option']
        return {'success':True, 'redirect':request.fwd_url("website_checkout_arbiter")}

class JoinLoginForm(LoginForm):
    fields = [
        EmailField("email", "Email", REQUIRED)
        , PasswordField("pwd", "Password", REQUIRED)
    ]
    @classmethod
    def on_success(cls, request, values):
        result = super(JoinLoginForm, cls).on_success(request, values)
        if result.get("success"):
            return {'success':True, 'redirect':request.fwd_url("website_checkout_arbiter")}
        else:
            return result

class JoinSignupForm(SignupForm):
    @classmethod
    def on_success(cls, request, values):
        result = super(JoinSignupForm, cls).on_success(request, values)
        if result.get("success"):
            return {'success':True, 'redirect':request.fwd_url("website_checkout_arbiter")}
        else:
            return result



class CheckoutForm(BaseForm):
    classes = 'form-horizontal form-validated'
    action_label = "Buy your plan now"
    fields = [
        PaymentOptionField("paymentOptionToken", None, "PaymentOption", default_none = False)
        , PlainHeadingField("Credit Card")
        , ConfigChoiceField("method", "Card Type", "CardType", default_none=False)
        , StringField("holder", "Holder", REQUIRED)
        , StringField("number", "Number", REQUIRED, min = 13, max = 16)
        , StringField("cvs", "CVV", attrs = HtmlAttrs(required = True) , min = 3, max = 4)
        , CombinedField([ConfigChoiceField("expiryMonth", None, "ExpiryMonth", default_none=False), ConfigChoiceField("expiryYear", None, "ExpiryYear", default_none=False)], "Expiration", REQUIRED)
        , PlainHeadingField("Billing address")
        , StringField("lastName", "Name", REQUIRED)
        , StringField("firstName", "Surname", REQUIRED)
        , StringField("line1", "Street", REQUIRED)
        , CombinedField([StringField("postCode", "Zip Code", REQUIRED, input_classes="input-mini"), StringField("city", "City", REQUIRED, input_classes="input-medium")], "Post code / City", REQUIRED)
        , StringField("country", "Country", REQUIRED)
        , CheckboxPostField("agreeTOS", u"Yes, I have read the Terms and Conditions and Agree.")
    ]
    @classmethod
    def on_success(cls, request, values):
        values['userToken'] = request.root.user.token
        result = PurchaseCreditProc(request, values)
        status = result.get('PaymentStatus')
        if status and status.get('success') == True:
            RefreshUserProfileProc(request, {'token':request.root.user.token})
            return {'success':True, 'redirect':request.fwd_url("website_cart")}
        else:
            return {'success':False, "message":"Payment Failed", 'values':values, 'errors':{}}


class SpendCreditsForm(BaseForm):
    id="spend"

    @classmethod
    def on_success(cls, request, values):
        context = request.root
        values['token'] = context.user.token
        collectors = [{'id':val} for val in values.get('Collector', [])]
        if not collectors:
            return {'success':False, 'message': "No Profiles selected"}
        elif not context.cart.canSpend(context.user):
            return {'success':False, 'message': "Insufficient credits"}
        else:
            values['Collector'] = collectors
            result = SpendCreditProc(request, values)
            context.cart.empty()
        return {'success':True, 'redirect': request.fwd_url("website_index")}