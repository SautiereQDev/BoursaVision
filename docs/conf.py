# Configuration file for the Sphinx documentation builder.
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

project = 'Boursa Vision'
copyright = '2025, Quentin Sautiere'
author = 'Quentin Sautiere'
release = '1.0.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
    'sphinx.ext.intersphinx',
    'sphinx.ext.autosummary',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.ifconfig',
    'sphinx_copybutton',
    'sphinxcontrib.mermaid',
    'myst_parser',
    'nbsphinx',
    'sphinxcontrib.plantuml',
    'sphinx_tabs.tabs',  # nom correct avec underscore
    'sphinxext.opengraph',
    'sphinx_design',
    'sphinxcontrib.bibtex',
    'sphinxcontrib.video',
    'sphinxemoji.sphinxemoji',
    'sphinx_autodoc_typehints',
]

# Exemples d'utilisation avancée (voir documentation officielle de chaque extension) :
# - .. tabs:: pour des onglets interactifs
# - .. grid:: et .. card:: pour des mises en page modernes
# - .. uml:: pour des diagrammes UML
# - .. mermaid:: pour des diagrammes Mermaid
# - .. video:: pour intégrer des vidéos
# - :emoji:`rocket` pour insérer des emojis
# - .. bibliography:: pour la bibliographie

# Génération automatique des fichiers autosummary
autosummary_generate = True

# Intersphinx : liens vers la doc Python standard et autres libs
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'fastapi': ('https://fastapi.tiangolo.com/', None),
    'pandas': ('https://pandas.pydata.org/pandas-docs/stable/', None),
}

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_logo = '_static/logo.png'
html_favicon = '_static/favicon.ico'
html_theme_options = {
    'logo_only': True,
    'display_version': True,
    'collapse_navigation': False,
    'navigation_depth': 4,
    'sticky_navigation': True,
    'style_nav_header_background': '#0d47a1',
}

# Ajoute le bouton "copier" sur tous les blocs de code
copybutton_prompt_text = r">>> |\.\.\. "
copybutton_prompt_is_regexp = True

# Support Markdown avancé (MyST)
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "html_admonition",
    "html_image",
    "linkify",
    "substitution",
    "tasklist",
]

# Napoleon settings for Google/NumPy style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True

# TODOs visibles dans la doc HTML
todo_include_todos = True

# Configuration de sphinxcontrib-bibtex
bibtex_bibfiles = ['references.bib']  # remplace par le nom et chemin de ton fichier .bib
bibtex_default_style = 'plain'        # style de citation par défaut (p.ex. plain, alpha, unsrt)
