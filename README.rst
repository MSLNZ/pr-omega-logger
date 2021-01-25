Logs the temperature, humidity and dew point from OMEGA iServer's to a database and creates a
Dash_ webapp to view the data. The information in the database can be viewed via a web browser,
at the URL ``http://<hostname>:<port>``.

Install
=======
.. code-block:: console

   pip install https://github.com/MSLNZ/pr-omega-logger/archive/master.tar.gz

Usage
=====
.. code-block:: console

   omega-logger /path/to/config.xml

Example config.xml
==================
Requires a Configuration File that is compatible with `MSL-Equipment`_

.. code-block:: xml

    <?xml version="1.0" encoding="utf-8"?>
    <msl>

        <log_dir>D:\OMEGA</log_dir>

        <serials>
            4370757
            12481415
        </serials>

        <calibrations>
            <!-- the coefficients value equals the polynomial coefficients c0;c1;c2;c3;... -->
            <omega serial="4370757">
                <report date="2018-07-21" number="Humidity/2018/386">
                    <start_date>2018-06-08</start_date>
                    <end_date>2018-06-11</end_date>
                    <coverage_factor>2.0</coverage_factor>
                    <confidence>95%</confidence>
                    <temperature units="C" min="18" max="24">
                        <coefficients>0.01</coefficients>
                        <expanded_uncertainty>0.13</expanded_uncertainty>
                    </temperature>
                    <humidity units="%rh" min="30" max="85">
                        <coefficients>-9.5;0.326;-0.00505;0.0000321</coefficients>
                        <expanded_uncertainty>0.9</expanded_uncertainty>
                    </humidity>
                </report>
                <report date="2016-02-22" number="Humidity/2016/322">
                    <start_date>2016-01-20</start_date>
                    <end_date>2016-01-22</end_date>
                    <coverage_factor>2.0</coverage_factor>
                    <confidence>95%</confidence>
                    <temperature units="C" min="17" max="23">
                        <coefficients>0.05</coefficients>
                        <expanded_uncertainty>0.12</expanded_uncertainty>
                    </temperature>
                    <humidity units="%rh" min="30" max="80">
                        <coefficients>-3.44;0.0487</coefficients>
                        <expanded_uncertainty>0.8</expanded_uncertainty>
                    </humidity>
                </report>
            </omega>
            <omega serial="12481415">
                <report date="2018-07-21" number="Humidity/2018/388">
                    <start_date>2018-06-08</start_date>
                    <end_date>2018-06-11</end_date>
                    <coverage_factor>2.0</coverage_factor>
                    <confidence>95%</confidence>
                    <temperature units="C" min="18" max="24">
                        <coefficients>0.04;0.13</coefficients>
                        <expanded_uncertainty>0.13</expanded_uncertainty>
                    </temperature>
                    <humidity units="%rh" min="30" max="85">
                        <coefficients>-10.2;0.393;-0.00637;0.000039</coefficients>
                        <expanded_uncertainty>1.0</expanded_uncertainty>
                    </humidity>
                </report>
            </omega>
        </calibrations>

        <registers>
            <register>
                <path>D:\QUAL\EquipmentRegister.xls</path>
                <sheet>Equipment</sheet>
            </register>
        </registers>

        <connections>
            <connection>
                <path>D:\QUAL\EquipmentRegister.xls</path>
                <sheet>OMEGA loggers</sheet>
            </connection>
        </connections>

    </msl>

.. _MSL-Equipment: https://msl-equipment.readthedocs.io/en/latest/
.. _Dash: https://plot.ly/products/dash/
