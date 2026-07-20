#!/bin/sh
nginx && gunicorn app:app
