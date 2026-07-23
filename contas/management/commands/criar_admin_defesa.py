from django.core.management.base import BaseCommand

from contas.models import Utilizador


class Command(BaseCommand):
    help = 'Cria ou atualiza o administrador usado na defesa.'

    def handle(self, *args, **options):
        email = 'jason@agrovision.local'
        user, created = Utilizador.objects.get_or_create(
            email=email,
            defaults={
                'nome_completo': 'Jason Molero',
                'tipo_utilizador': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
                'ativo_sistema': True,
            },
        )

        user.nome_completo = 'Jason Molero'
        user.tipo_utilizador = 'admin'
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.ativo_sistema = True
        user.set_password('AD251215')
        user.save()

        acao = 'criado' if created else 'atualizado'
        self.stdout.write(self.style.SUCCESS(
            f'Administrador {acao}: {email} / AD251215'
        ))
