from django import template

try:
    from phonenumbers import PhoneNumberFormat, format_number, parse
except ImportError:
    def format_phonenumber(value, arg=None):
        """As backup, render phonenumber in E.164 format."""
        return value
else:
    def format_phonenumber(value, arg='international'):
        """Formats a phonenumber according to the country's convenience."""
        phone_number = parse(value, None)
        num_format = PhoneNumberFormat.NATIONAL if arg == 'national' else PhoneNumberFormat.INTERNATIONAL
        return format_number(phone_number, num_format)

register = template.Library()
register.filter('format_phonenumber', format_phonenumber)
