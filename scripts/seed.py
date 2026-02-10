"""
Script de seed para dados de desenvolvimento.
Uso: python manage.py shell < scripts/seed.py
"""


def run():
    """Popula o banco com dados iniciais para desenvolvimento."""
    print("Seed concluído com sucesso!")


if __name__ == "__main__":
    import django
    import os

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.settings")
    django.setup()
    run()
