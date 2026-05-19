import os
from playsched import create_app

app = create_app()

if __name__ == "__main__":
    from config import Config

    host = Config.FLASK_RUN_HOST
    port = Config.FLASK_RUN_PORT
    debug_mode = Config.FLASK_DEBUG

    cert_file = Config.FLASK_CERT_FILE
    key_file = Config.FLASK_KEY_FILE

    ssl_context_mode = None
    if cert_file and key_file and os.path.exists(cert_file) and os.path.exists(key_file):
        ssl_context_mode = (cert_file, key_file)
        print("--- Using Custom SSL Certificate ---")
        print(f"  Cert File: {cert_file}")
        print(f"  Key File:  {key_file}")
        print(f"  Access via: https://localhost:{port} or https://127.0.0.1:{port}")
    else:
        if cert_file or key_file:
            print("--- WARNING: Custom SSL cert/key specified but not found/valid ---")
        else:
            print("--- Custom SSL cert/key not specified ---")
        print("--- Using 'adhoc' SSL context ---")
        ssl_context_mode = "adhoc"
        print("  Requires pyOpenSSL (pip install pyOpenSSL).")
        print(f"  Access via: https://localhost:{port} or https://127.0.0.1:{port}")
        print("  NOTE: Your browser WILL show a security warning.")

    print(" * Starting Spotify Flask app with HTTPS...")
    if debug_mode:
        print(" * Debug mode is ON")

    try:
        app.run(host=host, port=port, debug=debug_mode, ssl_context=ssl_context_mode)
    except ImportError:
        print("\nERROR: pyOpenSSL not found, required for 'adhoc' SSL.")
        print("       Please install it: pip install pyOpenSSL")
    except FileNotFoundError as e:
        print(f"\nERROR: Could not find certificate or key file: {e}\n")
    except OSError as e:
        print(f"\nERROR starting Flask server: {e}\n")
