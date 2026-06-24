"""
main.py
--------
Punto de entrada. No debería tener lógica - solo crear el Game y arrancarlo.
Ejecutar siempre desde la carpeta raíz del proyecto (pollo-cosmico/):

    python main.py
"""



from src.core.game import Game


def main() -> None:
    game = Game()
    game.run()


if __name__ == "__main__":
    main()



