# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import inspect
import os
import sys

import django
from django.urls import get_resolver
from django.utils.encoding import force_text
from django.utils.html import strip_tags

sys.path.insert(0, os.path.abspath('..'))

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.development"

django.setup()
# -- Project information -----------------------------------------------------

project = 'Small_EOD'
copyright = '2020, Sieć Obywatelska - Watchdog Polska'
author = 'Sieć Obywatelska - Watchdog Polska'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.coverage",
    "sphinx.ext.napoleon",
    "sphinx.ext.graphviz"
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "django": (
        "https://docs.djangoproject.com/en/3.1/",None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/contents.html", None),
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = 'pl'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
try:
    import sphinx_rtd_theme

    html_theme = "sphinx_rtd_theme"

    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
except ImportError:
    html_theme = "alabaster"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

def process_django_model(app, what, name, obj, options, lines):
    # This causes import errors if left outside the function
    from django.db import models

    # Only look at objects that inherit from Django's base model class
    if inspect.isclass(obj) and issubclass(obj, models.Model):
        # Grab the field list from the meta class
        fields = obj._meta.fields

        for field in fields:
            # Decode and strip any html out of the field's help text
            help_text = strip_tags(force_text(field.help_text))

            # Decode and capitalize the verbose name, for use if there isn't
            # any help text
            verbose_name = force_text(field.verbose_name).capitalize()

            if help_text:
                # Add the model field to the end of the docstring as a param
                # using the help text as the description
                lines.append(":param {}: {}".format(field.attname, help_text))
            else:
                # Add the model field to the end of the docstring as a param
                # using the verbose name as the description
                lines.append(":param {}: {}".format(field.attname, verbose_name))

            # Add the field's type to the docstring
            if isinstance(
                field, (models.ForeignKey, models.OneToOneField, models.ManyToManyField)
            ):
                lines.append(
                    ":type %s: %s to :class:`%s.%s`"
                    % (
                        field.attname,
                        type(field).__name__,
                        field.related_model.__module__,
                        field.related_model.__name__,
                    )
                )
            else:
                lines.append(":type {}: {}".format(field.attname, type(field).__name__))
    # Return the extended docstring
    return lines


def process_django_view(app, what, name, obj, options, lines):
    res = get_resolver()
    flat_patterns = []

    def walker(flat_patterns, urlpatterns, namespace=None):
        for pattern in urlpatterns:
            if hasattr(pattern, "url_patterns"):
                walker(flat_patterns, pattern.url_patterns, pattern.namespace)
            else:
                urlname = (
                    "{}:{}".format(namespace, pattern.name)
                    if namespace
                    else pattern.name
                )
                flat_patterns.append([urlname, pattern.callback])

    walker(flat_patterns, res.url_patterns)
    for urlname, callback in flat_patterns:
        if (
            hasattr(callback, "view_class") and callback.view_class == obj
        ) or callback == obj:
            lines.append(":param url_name: ``%s``\n" % urlname)
    return lines


def process_django_form(app, what, name, obj, options, lines):
    from django import forms

    if inspect.isclass(obj) and issubclass(obj, (forms.Form, forms.ModelForm)):
        for fieldname, field in obj.base_fields.items():
            lines.append(":param {}: {}".format(fieldname, field.label))


def setup(app):
    app.connect("autodoc-process-docstring", process_django_model)
    app.connect("autodoc-process-docstring", process_django_view)
    app.connect("autodoc-process-docstring", process_django_form)