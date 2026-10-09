Additive Service using Docker
=============================

Install the PyAdditive image
----------------------------

#. Using your GitHub credentials, download the Docker image from the `PyAdditive <https://github.com/pyansys/pyadditive>`_ repository.
#. If you have Docker installed, use a GitHub personal access token (PAT) with packages read permission to authorize Docker
   to access this repository. For more information,
   see `creating a personal access token <https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token>`_.

#. Save the token to a file:

   .. code:: bash

      echo XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX > GH_TOKEN.txt

#. Authorize Docker to access the repository:

   .. code:: bash

      GH_USERNAME=<my-github-username>
      cat GH_TOKEN.txt | docker login docker.pkg.github.com -u $GH_USERNAME --password-stdin

#. Launch the PyAdditive Service locally using ``docker`` with:

   .. code:: bash

      docker run --name additive -p 50052:50052 ghcr.io/pyansys/pygeometry:latest


Connect to Additive Service
---------------------------

After launching, connect to the service with:

.. code:: python

   >>> import ansys.additive as pyadditive
   >>> additive = pyadditive.launch_additive(ip='localhost', port=50052)
