SUPPORTED_LANGUAGES = [
    {"code": "en", "name": "English", "group": "International"},
    {"code": "hi", "name": "Hindi", "group": "Indian"},
    {"code": "te", "name": "Telugu", "group": "Indian"},
    {"code": "ta", "name": "Tamil", "group": "Indian"},
    {"code": "ml", "name": "Malayalam", "group": "Indian"},
    {"code": "kn", "name": "Kannada", "group": "Indian"},
    {"code": "bn", "name": "Bengali", "group": "Indian"},
    {"code": "mr", "name": "Marathi", "group": "Indian"},
    {"code": "gu", "name": "Gujarati", "group": "Indian"},
    {"code": "pa", "name": "Punjabi", "group": "Indian"},
    {"code": "ur", "name": "Urdu", "group": "Indian"},
    {"code": "or", "name": "Odia", "group": "Indian"},
    {"code": "as", "name": "Assamese", "group": "Indian"},
    {"code": "sa", "name": "Sanskrit", "group": "Indian"},
    {"code": "es", "name": "Spanish", "group": "International"},
    {"code": "fr", "name": "French", "group": "International"},
    {"code": "de", "name": "German", "group": "International"},
    {"code": "it", "name": "Italian", "group": "International"},
    {"code": "pt", "name": "Portuguese", "group": "International"},
    {"code": "ru", "name": "Russian", "group": "International"},
    {"code": "ar", "name": "Arabic", "group": "International"},
    {"code": "zh-CN", "name": "Chinese", "group": "International"},
    {"code": "ja", "name": "Japanese", "group": "International"},
    {"code": "ko", "name": "Korean", "group": "International"},
    {"code": "id", "name": "Indonesian", "group": "International"},
    {"code": "tr", "name": "Turkish", "group": "International"},
]

SUPPORTED_LANGUAGE_CODES = {language["code"] for language in SUPPORTED_LANGUAGES}


def detect_script_language(text):
    if not text:
        return "unknown"

    script_ranges = [
        ("te", 0x0C00, 0x0C7F),
        ("ta", 0x0B80, 0x0BFF),
        ("kn", 0x0C80, 0x0CFF),
        ("ml", 0x0D00, 0x0D7F),
        ("bn", 0x0980, 0x09FF),
        ("gu", 0x0A80, 0x0AFF),
        ("pa", 0x0A00, 0x0A7F),
        ("or", 0x0B00, 0x0B7F),
        ("hi", 0x0900, 0x097F),
        ("ur", 0x0600, 0x06FF),
    ]

    counts = {code: 0 for code, _, _ in script_ranges}
    for char in text:
        codepoint = ord(char)
        for language_code, start, end in script_ranges:
            if start <= codepoint <= end:
                counts[language_code] += 1

    language_code, count = max(counts.items(), key=lambda item: item[1])
    return language_code if count > 0 else "en"
