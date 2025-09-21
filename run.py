from app import create_app   # importa la función

app = create_app()           # crea la aplicación

if __name__ == "__main__":
    app.run(debug=True)
