Used to log the temperature, humidity and dew point from an OMEGA iServer to a SQLite database.
The information in the database can be accessed via a web browser.

Install
=======
pip install git+https://github.com/MSLNZ/omega-logger.git --process-dependency-links

Usage
=====
.. code-block:: console

    omega-logger start /path/to/config.xml

Example config.xml
==================
Requires a Configuration File that is compatible with `MSL-Equipment`_

.. code-block:: xml

    <?xml version="1.0" encoding="utf-8"?>
    <msl>

        <log_dir>D:\OMEGA</log_dir>

        <serials>
            4070777
            4100593
            17480215
        </serials>

        <calibrations>
            <!-- the coefficients value equals the polynomial coefficients c0;c1;c2;c3;... -->
            <omega serial="4070777">
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
            <omega serial="4100593">
                <report date="2018-07-21" number="Humidity/2018/387">
                    <start_date>2018-06-08</start_date>
                    <end_date>2018-06-11</end_date>
                    <coverage_factor>2.0</coverage_factor>
                    <confidence>95%</confidence>
                    <temperature units="C" min="18" max="24">
                        <coefficients>0.44;-0.019</coefficients>
                        <expanded_uncertainty>0.13</expanded_uncertainty>
                    </temperature>
                    <humidity units="%rh" min="30" max="85">
                        <coefficients>-9.2;0.375;-0.00608;0.0000371</coefficients>
                        <expanded_uncertainty>1.0</expanded_uncertainty>
                    </humidity>
                </report>
                <report date="2016-02-22" number="Humidity/2016/323">
                    <start_date>2016-01-20</start_date>
                    <end_date>2016-01-22</end_date>
                    <coverage_factor>2.0</coverage_factor>
                    <confidence>95%</confidence>
                    <temperature units="C" min="17" max="23">
                        <coefficients>0.05</coefficients>
                        <expanded_uncertainty>0.14</expanded_uncertainty>
                    </temperature>
                    <humidity units="%rh" min="30" max="80">
                        <coefficients>-2.42;0.0449</coefficients>
                        <expanded_uncertainty>0.9</expanded_uncertainty>
                    </humidity>
                </report>
            </omega>
            <omega serial="17480215">
                <report date="2018-07-21" number="Humidity/2018/388">
                    <start_date>2018-06-08</start_date>
                    <end_date>2018-06-11</end_date>
                    <coverage_factor>2.0</coverage_factor>
                    <confidence>95%</confidence>
                    <temperature units="C" min="18" max="24">
                        <coefficients>0.0</coefficients>
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
                <path>D:\OMEGA\EquipmentRegister.xls</path>
                <sheet>Equipment</sheet>
            </register>
        </registers>

        <connections>
            <connection>
                <path>D:\OMEGA\EquipmentRegister.xls</path>
                <sheet>OMEGA loggers</sheet>
            </connection>
        </connections>

    </msl>

.. _MSL-Equipment: https://msl-equipment.readthedocs.io/en/latest/