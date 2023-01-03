Running the additive service
############################

Start the additive Docker image
-------------------------------

#. If you have Docker installed, use a GitHub personal access token (PAT) with packages read permission to authorize Docker
   to access the container registry. For more information,
   see `creating a personal access token <https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token>`_.
   Make sure to save your token in a file or an environment variable for later reference.

#. Authorize Docker to access the repository by saving your token to your clipboard then pasting it (``Ctrl-V``) when prompted for
   your password in the following command. Note that you may not get any indication that your token was pasted, just hit ``Enter``
   after pasting.

   .. code:: bash

      docker login ghcr.io

#. On Windows:

#. Launch the PyAdditive service locally using ``docker`` with:

   .. code:: bash

      docker run --name additive -p 50052:50052 ghcr.io/pyansys/additive:latest


Connect to additive service
---------------------------

After launching the service, connect to the service inside a python environment
with:

.. code:: python

   >>> import ansys.additive as pyadditive
   >>> additive = pyadditive.launch_additive(ip='localhost', port=50052)
