from website import create_app
import os

if __name__ == '__main__':
    app = create_app()
    app.run(host="0.0.0.0", threaded=True, port=int(os.environ.get('PORT', 33507)))
