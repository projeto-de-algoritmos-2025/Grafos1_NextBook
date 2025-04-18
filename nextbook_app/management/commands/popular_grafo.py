import random
from django.core.management.base import BaseCommand
from nextbook_app.models import Livro, GrafoLivros

class Command(BaseCommand):
    help = 'Popula o grafo de recomendações com conexões aleatórias'

    def handle(self, *args, **options):
        livros = list(Livro.objects.all())
        if not livros:
            self.stdout.write(self.style.ERROR('Nenhum livro encontrado!'))
            return

        novas_conexoes = 0
        total_livros = len(livros)

        for i, livro_origem in enumerate(livros):
            livros_destino = random.sample(
                [livro for livro in livros if livro != livro_origem],
                min(3, total_livros - 1)
            )

            for livro_destino in livros_destino:
                _, created = GrafoLivros.objects.get_or_create(
                    livro_origem=livro_origem,
                    livro_destino=livro_destino,
                    defaults={'peso': random.randint(1, 5)}
                )
                if created:
                    novas_conexoes += 1

        self.stdout.write(self.style.SUCCESS(
            f'Grafo populado! {novas_conexoes} novas conexões criadas. '
            f'Total: {GrafoLivros.objects.count()} conexões.'
        ))
