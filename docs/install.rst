Installation
============

Overview
^^^^^^^^
oTree Manager uses Docker to containerize both databases and the actual oTree installations. Container management is handled by Dokku. The web interfaces is written in Python (3) and builds upon Django in combination with Django-Channels for running background tasks. The web interface requires PostgreSQL and Redis databases to store its data and handle user sessions. Supervisor keeps the web interface as well as the background task worker running. Nginx serves as a reverse proxy for the oTree installations and handles routing of requests between the oTree instance containers and the web interface.

Currently, I only recommend installations on Debian-based operating systems and write the installation instructions for a fresh installation of Debian 9. I have not tried other systems but do not see many reasons why it would not work. However, there is no Dokku release for Windows, so running this on a Windows machine will not work.
