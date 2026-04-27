from django.db import migrations


def create_agentsite(apps, schema_editor):
    User = apps.get_model('users', 'User')
    AgentSite = apps.get_model('constructor', 'AgentSite')

    # Знаходимо суперадміна
    admin = User.objects.filter(is_superuser=True).first()
    if admin and not AgentSite.objects.filter(user=admin).exists():
        AgentSite.objects.create(
            user=admin,
            slug='main-site',
            agency_name='TourConstructor',
            show_superadmin_tours=True
        )
        print(f"✅ Створено AgentSite для {admin.username}")


class Migration(migrations.Migration):
    dependencies = [
        ('constructor', '0005_alter_agentsite_primary_color_and_more'),
    ]
    operations = [migrations.RunPython(create_agentsite)]