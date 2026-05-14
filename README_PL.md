# PlaySched – Harmonogram Odtwarzania Playlist Spotify

[![Licencja: MIT](https://img.shields.io/badge/Licencja-MIT-żółty.svg)](https://opensource.org/licenses/MIT)

![Ikona Aplikacji](static/android-chrome-192x192.png)

[Historia Wersji](VERSION.md) – Aktualna Wersja: v0.2.0 – 14 maja 2026

[Plan Rozwoju](ROADMAP.md)

Projekt łączący aplikację webową do planowania odtwarzania playlist Spotify z narzędziem wiersza poleceń do bezpośredniej kontroli Spotify, zarządzania historią i synchronizacji danych.

Aplikacja będzie się rozwijać z czasem. Obecnie rozwiązuje jeden konkretny problem – zdałem sobie sprawę, że jedynym powodem, dla którego używam Amazon Alexy™, jest odtwarzanie/zatrzymywanie muzyki o określonych godzinach (i w określone dni). Interfejs Alexy do tego celu jest okropny. Teraz mogę odłączyć Alexę i używać znacznie lepszych głośników w laptopie za pośrednictwem aplikacji Spotify, sterowanej przez tę aplikację harmonogramu. Zobacz [Plan Rozwoju](ROADMAP.md), aby dowiedzieć się, co może pojawić się w przyszłości. Może. Jeśli nie zacznę się rozpraszać innymi błyszczącymi rzeczami, teraz gdy ten konkretny problem został rozwiązany.

## Przegląd

* **Aplikacja Webowa (`playsched.py`):** Zapewnia przyjazny interfejs webowy do planowania odtwarzania playlist Spotify na konkretnych urządzeniach o ustalonych porach. Obejmuje opcje powtarzalności (dni tygodnia), godziny startu/stopu, głośność i tryb losowy. Pozwala zarządzać utworzonymi harmonogramami (edycja, duplikowanie, pauza, usuwanie).
* **Skrypt Wiersza Poleceń (`play_spotify_playlist.py`):** Oferuje bezpośrednią interakcję z terminalem ze Spotify: listowanie urządzeń/playlist, uruchamianie odtwarzania, zarządzanie lokalną bazą danych historii odtwarzania, synchronizowanie wszystkich playlist i utworów lokalnie oraz eksportowanie tych danych.

## Funkcje

### Funkcje Aplikacji Webowej (`playsched.py`)

* **Uwierzytelnianie Spotify:** Bezpieczne logowanie za pomocą konta Spotify (OAuth 2.0).
* **Przeglądanie Playlist:** Przeglądanie i filtrowanie playlist Spotify.
* **Lista Urządzeń:** Automatyczne wykrywanie dostępnych urządzeń Spotify Connect.
* **Harmonogramowanie:**
    * Wybierz playlistę i docelowe urządzenie.
    * Ustaw godzinę startu (GG:MM) i opcjonalną godzinę stopu (GG:MM).
    * Określ dni tygodnia dla harmonogramów cyklicznych (lub zostaw puste dla jednorazowego odtwarzania).
    * Ustaw głośność odtwarzania (opcjonalnie).
    * Włącz/wyłącz tryb losowy dla odtwarzania.
    * Określ strefę czasową harmonogramu.
* **Zarządzanie Harmonogramami:**
    * Przeglądaj wszystkie utworzone harmonogramy, posortowane według czasu następnego uruchomienia.
    * Ręcznie uruchom odtwarzanie ("Odtwórz Teraz").
    * Zatrzymaj odtwarzanie natychmiastowo ("Zatrzymaj Teraz").
    * Wstrzymaj/wznów harmonogramy (przełączanie stanu aktywnego).
    * Edytuj istniejące harmonogramy.
    * Duplikuj istniejące harmonogramy, aby łatwo tworzyć warianty.
    * Usuwaj harmonogramy.
* **Widget Teraz Gra:** Dynamiczne wyświetlanie aktualnie odtwarzanego utworu (tytuł, wykonawca, okładka albumu, pasek postępu z czasem), nazwy aktywnego urządzenia oraz następnego utworu w kolejce. Odświeża się automatycznie co 5 sekund.
* **Zegar na Żywo:** Aktualna data i godzina wyświetlane wyraźnie w nagłówku, z sekundowym odświeżaniem i czytelną czcionką monospace.
* **Motyw Ciemny:** Pełny przełącznik motywu ciemnego/jasnego z wykrywaniem preferencji systemowych i zapisywaniem w `localStorage`.
* **Harmonogram w Tle:** Używa APScheduler do automatycznego uruchamiania/zatrzymywania odtwarzania zgodnie z zdefiniowanymi harmonogramami.

### Funkcje Skryptu Wiersza Poleceń (`play_spotify_playlist.py`)

* **Lista Urządzeń:** Wyświetla dostępne urządzenia Spotify Connect.
* **Lista Playlist:** Pokazuje playlisty bezpośrednio ze Spotify.
* **Kontrola Odtwarzania:** Rozpocznij odtwarzanie określonej playlisty na wybranym urządzeniu bezpośrednio z wiersza poleceń.
* **Historia Odtwarzania:**
    * Pobiera ostatnio odtwarzane utwory ze Spotify.
    * Przechowuje tę historię w lokalnej bazie danych SQLite.
    * Wyświetla ostatnio odtwarzane playlisty na podstawie zapisanej historii (z konwersją na lokalny czas).
* **Pełna Synchronizacja Playlist:**
    * Pobiera wszystkie playlisty (utworzone i obserwowane) oraz ich utwory ze Spotify.
    * Przechowuje te dane w lokalnych tabelach SQLite (`synced_playlists`, `synced_playlist_tracks`).
    * Oznacza playlisty lub utwory jako "usunięte", jeśli nie są już znalezione w bibliotece Spotify, bez usuwania ich z bazy danych.
* **Eksport Danych:**
    * Eksportuje zsynchronizowane playlisty i utwory z lokalnej bazy danych.
    * Wspiera eksport do Excela (`.xlsx` z osobnymi arkuszami dla playlist i utworów), CSV (generuje dwa pliki: `*_playlists.csv` i `*_tracks.csv`) lub JSON (`.json` ze strukturą danych).

![Przeglądanie Playlist](img/screenshot-browse-playlists.jpg)

![Harmonogram Playlisty](img/screenshot-schedule.jpg)

![Przeglądanie i Aktualizacja Playlist](img/screenshot-view-update.jpg)

## Wymagania Wstępne

* **Python:** Zalecana wersja 3.8 lub wyższa.
* **pip lub conda:** Do instalacji pakietów.
* **OpenSSL:** Wymagany do generowania certyfikatów (zazwyczaj preinstalowany na Linux/macOS, do pobrania dla Windows).
* **Konto Spotify:** Zwykłe lub Premium.
* **Dane Aplikacji Spotify Developer:** Musisz zarejestrować aplikację w Spotify Developer Dashboard, aby uzyskać klucze API. Szczegółowe kroki poniżej.
* **Dla Funkcji Eksportu:** Biblioteki Pythona `pandas` i `openpyxl` (zobacz sekcję Instalacja w `requirements.txt`).

### Konfiguracja Aplikacji Spotify Developer

Aby umożliwić tej aplikacji interakcję z Twoim kontem Spotify, musisz ją zarejestrować na platformie deweloperskiej Spotify:

1.  **Przejdź do Spotify Developer Dashboard:** Otwórz [https://developer.spotify.com/dashboard/](https://developer.spotify.com/dashboard/) w przeglądarce.
2.  **Zaloguj się:** Użyj swoich danych logowania do konta Spotify.
3.  **Utwórz Aplikację:** Kliknij **"Create App"** (lub "Create an app"), wypełnij nazwę i opis, zaakceptuj warunki i kliknij **"Create"**.
4.  **Pobierz Dane Logowania:** Na pulpicie aplikacji skopiuj swój **Client ID**. Kliknij **"Show client secret"**, aby wyświetlić i skopiować swój **Client Secret**. Zachowaj sekret w poufności.
5.  **Skonfiguruj Ustawienia:** Kliknij **"Edit Settings"** (lub znajdź sekcję ustawień dla swojej aplikacji).
    * **Website:** Musisz podać adres URL strony. Dla lokalnego rozwoju możesz użyć lokalizacji serwera Flask (np. `https://127.0.0.1:9093`).
    * **Redirect URIs:** Dodaj dokładny URI, którego aplikacja użyje do callbacków. Dla tego projektu używającego HTTPS na domyślnym porcie `9093`, dodaj:
        ```
        https://127.0.0.1:9093/callback
        ```
        * Użyj `127.0.0.1` zamiast `localhost` – localhost może czasem powodować problemy z walidacją callbacków lub politykami bezpieczeństwa przeglądarki.
        * Upewnij się, że to **dokładnie pasuje** do `SPOTIPY_REDIRECT_URI` w Twoim pliku `.env`. Dodaj jeden URI na linię.
    * Kliknij **"Save"** na dole strony ustawień.
6.  **Użyj Danych Logowania:** Skopiuj Client ID i Client Secret do pliku `.env`.

## Instalacja

1.  **Sklonuj Repozytorium:**
    ```bash
    git clone https://github.com/storizzi/playsched
    cd playsched
    ```

2.  **Utwórz Środowisko Wirtualne (Zalecane):**

    * **Używając `venv` (standardowy Python):**
        ```bash
        # Utwórz środowisko (uruchom raz)
        python -m venv venv

        # Aktywuj środowisko
        # Na Windows (cmd/powershell):
        .\venv\Scripts\activate
        # Na macOS/Linux (bash/zsh):
        source venv/bin/activate
        ```

    * **Używając `conda`:**
        ```bash
        # Utwórz środowisko (uruchom raz)
        conda create -n spotify-scheduler python=3.9

        # Aktywuj środowisko
        conda activate spotify-scheduler
        ```

3.  **Zainstaluj Zależności:**
    Upewnij się, że Twoje środowisko wirtualne jest aktywowane.
    ```bash
    pip install -r requirements.txt
    ```

## Konfiguracja (Plik `.env`)

Aplikacja używa zmiennych środowiskowych ładowanych z pliku `.env` w głównym katalogu projektu.

1.  Utwórz plik o nazwie `.env` w głównym katalogu projektu. Jest przykładowy plik `.env-sample`, który możesz skopiować jako szablon.
2.  Dodaj następujące zmienne, zastępując wartości placeholderów swoimi rzeczywistymi danymi logowania i preferowanymi ustawieniami:

    ```dotenv
    # Dane Spotify API (Wymagane)
    SPOTIPY_CLIENT_ID='TWÓJ_SPOTIFY_CLIENT_ID'
    SPOTIPY_CLIENT_SECRET='TWÓJ_SPOTIFY_CLIENT_SECRET'
    SPOTIPY_REDIRECT_URI='https://127.0.0.1:9093/callback'

    # Konfiguracja Flask (Wymagane)
    SECRET_KEY='TWÓJ_SILNY_LOSOWY_KLUCZ'
    FLASK_DEBUG=1

    # Ustawienia Wspólne (Wymagane)
    SCHEDULE_DB_FILE='playsched.db'
    SPOTIPY_CACHE_PATH='.spotify_token_cache.json'
    SCHEDULER_INTERVAL_SECONDS=15
    SCHEDULER_TIMEZONE='UTC'

    # Certyfikaty SSL dla HTTPS
    FLASK_CERT_FILE=localhost.crt
    FLASK_KEY_FILE=localhost.key
    ```

## HTTPS dla Lokalnego Rozwoju

Spotify API wymaga `https://` dla URI callbacków. Serwer deweloperski Flask musi być skonfigurowany do używania HTTPS.

**Opcja 1: Użycie Niestandardowych Certyfikatów (Zalecane)**

1.  **Wygeneruj Certyfikaty:**
    ```bash
    chmod +x generate_certs.zsh
    zsh generate_certs.zsh
    ```
    Tworzy to `myCA.pem` (certyfikat CA), `localhost.crt` (certyfikat serwera) i `localhost.key` (klucz serwera).

2.  **Zaufaj Swemu Certyfikatowi CA (`myCA.pem`):**
    * **Chrome:**
        * Przejdź do `chrome://settings/certificates`.
        * Zakładka **"Authorities"**.
        * Kliknij **"Import..."**.
        * Wybierz wygenerowany plik `myCA.pem`.
        * Zaznacz **"Trust this certificate for identifying websites"**.
        * Kliknij OK/Finish.
    * **macOS:**
        * Zaimportuj `myCA.pem` przez Keychain Access.
        * Znajdź zaimportowany certyfikat, kliknij dwukrotnie.
        * Rozwiń sekcję **Trust** i ustaw "When using this certificate:" na **"Always Trust"**.
    * **Windows:** Wyszukaj "Manage computer certificates", uruchom jako administrator. Przejdź do "Trusted Root Certification Authorities" > "Certificates". Zaimportuj `myCA.pem`.

3.  **Skonfiguruj Flask:** Dodaj do `.env`:
    ```dotenv
    FLASK_CERT_FILE=localhost.crt
    FLASK_KEY_FILE=localhost.key
    ```

4.  **Dostęp:** Przejdź do `https://localhost:9093` lub `https://127.0.0.1:9093`. Nie powinieneś widzieć ostrzeżenia o bezpieczeństwie, jeśli CA został zaufany.

**Opcja 2: Automatyczne Certyfikaty 'adhoc'**

1.  Upewnij się, że `pyOpenSSL` jest zainstalowany (`pip install pyOpenSSL`).
2.  **Nie ustawiaj** `FLASK_CERT_FILE` i `FLASK_KEY_FILE` w `.env` (zakomentuj je).
3.  Uruchom aplikację. Przejdź do `https://127.0.0.1:9093`. Przeglądarka pokaże ostrzeżenie – kliknij "Advanced" i wybierz kontynuowanie.

## Uruchamianie Aplikacji

### Uruchamianie Aplikacji Webowej

```bash
python playsched.py
```

Otwórz przeglądarkę i przejdź do `https://127.0.0.1:9093`.

### Uruchamianie Skryptu Wiersza Poleceń

```bash
python play_spotify_playlist.py --help
```

## Użytkowanie

### Użytkowanie Aplikacji Webowej

1.  **Logowanie:** Przejdź do adresu aplikacji i kliknij "Login with Spotify". Autoryzuj aplikację przez stronę Spotify.
2.  **Przeglądaj/Harmonogramuj:** Użyj zakładki "My Playlists", aby znaleźć playlisty. Kliknij "Schedule", aby otworzyć formularz.
3.  **Wypełnij Formularz:** Wybierz urządzenie, dni, godziny, głośność, tryb losowy i strefę czasową. Kliknij "Save Schedule".
4.  **Zarządzaj:** Użyj zakładki "Scheduled Playlists", aby przeglądać, odtwarzać teraz, zatrzymywać, wstrzymywać/wznawiać, edytować, duplikować lub usuwać harmonogramy.

### Użytkowanie Skryptu Wiersza Poleceń

* Lista dostępnych urządzeń:
    ```bash
    python play_spotify_playlist.py --list-devices
    ```
* Lista playlist:
    ```bash
    python play_spotify_playlist.py --list-playlists
    ```
* Aktualizacja lokalnej historii odtwarzania:
    ```bash
    python play_spotify_playlist.py --update-history
    ```
* Ostatnio odtwarzane playlisty z lokalnej bazy:
    ```bash
    python play_spotify_playlist.py --recent-playlists
    ```
* **Synchronizuj wszystkie playlisty do lokalnej bazy:**
    ```bash
    python play_spotify_playlist.py --sync-playlists
    ```
* **Eksportuj zsynchronizowane dane:**
    ```bash
    # Eksport do Excela
    python play_spotify_playlist.py --export-data moje_dane_spotify.xlsx

    # Eksport do CSV
    python play_spotify_playlist.py --export-data moje_dane_spotify.csv

    # Eksport do JSON
    python play_spotify_playlist.py --export-data moje_dane_spotify.json
    ```
* Odtwórz playlistę na konkretnym urządzeniu:
    ```bash
    python play_spotify_playlist.py --device "Moje Głośniki" --playlist "Chill Mix"
    ```

## Uwagi i Ograniczenia

* **Limity API Spotify:** Intensywne użytkowanie może potencjalnie przekroczyć limity API Spotify.
* **Dostępność Urządzenia:** Odtwarzanie wymaga, aby docelowe urządzenie było online i aktywne w Spotify. Akcje zawiodą, jeśli urządzenie jest niedostępne.
* **Precyzja Harmonogramu:** Zaplanowane zadania uruchamiają się na podstawie `SCHEDULER_INTERVAL_SECONDS`. Odtwarzanie może rozpocząć/zatrzymać się nieznacznie po dokładnej zaplanowanej minucie.
* **Strefy Czasowe i DST:** Upewnij się, że używasz prawidłowych nazw stref czasowych (nazwy bazy TZ). Backend używa `pytz` do obsługi stref czasowych i DST.
* **Pamięć Podręczna Tokena:** Plik `.spotify_token_cache.json` przechowuje token uwierzytelniania aplikacji webowej, używany przez harmonogram. Usunięcie wymaga ponownego logowania przez aplikację webową.
* **Bazy Danych:** `playsched.db` przechowuje harmonogramy aplikacji webowej, historię CLI oraz zsynchronizowane playlisty/utwory. Wykonuj kopie zapasowe, jeśli potrzebujesz.

## Wkład w Projekt

Wkłady są mile widziane! Zapraszamy do zgłaszania Pull Requestów lub otwierania Issues.

## Licencja

Ten projekt jest licencjonowany na licencji MIT – zobacz plik [LICENSE](LICENSE) dla szczegółów.
