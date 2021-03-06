from django.core.validators import EmailValidator
from rest_framework import serializers, fields
from rest_framework.generics import get_object_or_404
from core.models.user import User
from core.encoder.tokens import encode_user_id
from core.encoder.tokens import make_user_token
from core.models.queries.queryUser import HelperUser
from api.celery import send_email_module
from api.settings import development


URL_TO_SEND = development.URL_PRODUCTION


class UserSerializer(serializers.ModelSerializer):
    """serializer model user"""
    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'email',
            'password')
        extra_kwargs = {'password': {'write_only': True, 'min_length': 5},
                        'is_delete': {'write_only': True}}
        read_only_fields = ('id', )

    def create(self, validate_data):
        """create user and send email confirmation"""
        user_instance = User.objects.create_user(**validate_data)
        uid = encode_user_id(user_instance.id)
        token = make_user_token(user_instance)
        url = f'{URL_TO_SEND}/'
        context_page = '#/activation-account'
        email_context = {
            'fullname': f'{validate_data["first_name"]}',
            'domain': url + context_page,
            'uid': uid,
            'token': token}
        tmp_name = 'emails/send_email_confirmation.html'
        send_email_module.delay(
            subject='No reply',
            to=[validate_data['email'], ],
            body='',
            template_name=tmp_name,
            context=email_context)
        return user_instance

    def update(self, instance, validate_data):
        """update password from current user"""
        password = validate_data.pop('password', None)
        user = super().update(instance, validate_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class RecoveryPwdSerializer(serializers.ModelSerializer):
    """model recovery password serializer"""
    email = fields.EmailField(validators=[EmailValidator(), ])

    class Meta:
        model = User
        fields = ('email', )

    def create(self, validate_data):
        """send email to recovery password"""
        user = get_object_or_404(User, email=validate_data.get('email'))
        uid = encode_user_id(user.id)
        token = make_user_token(user)
        url = f'{URL_TO_SEND}'
        context_page = '#/recovery-password'
        email_context = {
            'fullname': f'{user.first_name}',
            'domain': url + context_page,
            'uid': uid,
            'token': token}
        tmp_name = 'emails/recovery_password_email.html'
        send_email_module.delay(
            subject='Cotizate - Recovery Password',
            to=[validate_data['email'], ],
            body='',
            template_name=tmp_name,
            context=email_context,
        )
        return validate_data


class PwdConfirmSerialzier(serializers.ModelSerializer):
    """confirm password serializer"""
    password = fields.CharField(
        style={'input_type': 'password'}, required=True,
    )
    password_confirm = fields.CharField(
        style={'input_type': 'password'}, required=True,
    )

    class Meta:
        model = User
        fields = ('password', 'password_confirm')

    def validate(self, attrs):
        """validation data password and password confirm"""
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError("Those passwords don't match")
        return attrs


class ActivateSerializer(serializers.ModelSerializer):
    """validate data email"""
    email = fields.EmailField(validators=[EmailValidator(), ])

    class Meta:
        model = User
        fields = ('email',)

    def create(self, validate_data):
        """send email to re activate account"""
        current = HelperUser()
        user = current.get_user_email(validate_data.get('email'))
        uid = encode_user_id(user.id)
        token = make_user_token(user)
        url = f'{URL_TO_SEND}'
        context_page = '#/res-send-email-account'
        email_context = {
            'fullname': f'{user.first_name}',
            'domain': url + context_page,
            'uid': uid,
            'token': token}
        tmp_name = 'emails/re_activate_account_email.html'
        send_email_module.delay(
            subject='Cotizate - Recovery Password',
            to=[validate_data['email'], ],
            body='',
            template_name=tmp_name,
            context=email_context,
        )
        return validate_data


class RActivateSerializer(serializers.ModelSerializer):
    """re-activate account serializer"""
    class Meta:
        model = User
        fields = ('email', )
