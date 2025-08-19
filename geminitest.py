import subprocess

def lemmatize_with_subprocess(text):
    """
    Lemmatizes a given text string by calling the voikko-lemmatize command-line
    tool via WSL.
    """
    # Suoritetaan komento WSL:n kautta. Huomaa, että työkalu on nyt "voikko-lemmatize".
    # Komento lukee syötteen (input) ja tulostaa jokaisen sanan perusmuodon omalle rivilleen.
    result = subprocess.run(
        ["wsl", "voikko-lemmatize", "-d", "fi"],
        input=text.encode("utf-8"),
        capture_output=True # capture_output=True on kätevämpi kuin stdout=PIPE, stderr=PIPE
    )

    # Tarkistetaan virheet
    if result.stderr:
        print("ERROR processing text:", text)
        print("Voikko Error:", result.stderr.decode("utf-8"))
        return text # Palautetaan alkuperäinen teksti virhetilanteessa

    # Dekoodataan tulos ja yhdistetään rivit takaisin yhdeksi lauseeksi välilyönneillä
    lemmatized_output = result.stdout.decode("utf-8").strip()
    lemmatized_text = ' '.join(lemmatized_output.splitlines())
    
    return lemmatized_text

lemmatize_with_subprocess("tietokonessa")
