"""Run only against aspm_rc1_validation. Creates one access-free local smoke user."""
import json
import sys
from django.contrib.auth import get_user_model
from django.db import connection
if connection.settings_dict['NAME']!='aspm_rc1_validation':raise RuntimeError('Requires isolated RC database')
secret=json.load(sys.stdin)
User=get_user_model()
user,created=User.objects.get_or_create(username=secret['username'],defaults={'is_active':True,'is_staff':False,'is_superuser':False})
if not created:raise RuntimeError('Namespace collision; existing user preserved')
user.set_password(secret['password']);user.save(update_fields=['password'])
print('Created isolated user without product permissions')
