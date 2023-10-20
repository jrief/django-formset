from django.contrib.staticfiles.storage import ManifestStaticFilesStorage


class NoSourceMapsManifestStaticStorage(ManifestStaticFilesStorage):
    patterns = (
        (
            "*.css",
            (
                "(?P<matched>url\\(['\"]{0,1}\\s*(?P<url>.*?)[\"']{0,1}\\))",
                (
                    "(?P<matched>@import\\s*[\"']\\s*(?P<url>.*?)[\"'])",
                    '@import url("%(url)s")',
                ),
            ),
        ),
        (
            "*.js",
            (
            ),
        ),
    )
