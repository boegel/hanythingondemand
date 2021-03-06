.. _browser_proxy_chrome_windows:

Browser proxy configuration for Chrome on Windows
=================================================

.. note::
  Keep in mind that using the proxy will only work while you have access to the workernode for which the SSH tunnel
  was set up, i.e. while the HOD cluster is running, and while you are able to connect to the HPC infrastructure.

  To reset your browser configuration back to normal, simply disable the proxy in your browser configuration.

1. Open ``Settings`` in Chrome, search for ``Change proxy settings`` button (and click it)

.. image:: img/browser_proxy_cfg/chrome-settings.png 

2. In the ``Internet Properties`` window, click ``LAN settings``

.. image:: img/browser_proxy_cfg/chrome_windows/01_internet_properties.png 

3. In the ``Local Area Network (LAN) settings`` window, enable ``Use a proxy server for your LAN``,
   and click ``Advanced``

.. image:: img/browser_proxy_cfg/chrome_windows/02_lan_settings.png

4. In the ``Proxy settings`` window, enter ``localhost`` as proxy address for the ``Socks`` proxy type, and
   enter the port number you used when setting up the SSH tunnel, e.g. ``12345`` or ``10000``.

   Click ``OK`` to save the configuration.

.. image:: img/browser_proxy_cfg/chrome_windows/03_proxy_settings.png
