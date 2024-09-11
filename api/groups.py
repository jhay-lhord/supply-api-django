from django.contrib.auth.models import Group


def create_groups():
    roles = ['Supply Officer', 'Budget Officer', 'BAC Officer', 'Admin']

    for role in roles:
        group, created = Group.objects.get_or_create(name=role)
        if created:
            print(f'{role} Group Created')


def assign_role(user, role_name):
    try:
        group = Group.objects.get(name=role_name)
        user.groups.add(group)
        user.save()
        print(f'{role_name} assign to {user} ')
    except Group.DoesNotExist:
        print(f'Role {role_name} Does Not Exist')
