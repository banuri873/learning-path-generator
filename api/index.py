from app import app

# This handles WSGI requests for Vercel serverless
def handler(request, response):
    return app(request, response)