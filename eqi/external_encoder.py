import os
import sys
import easyvvuq as uq
import importlib

__copyright__ = """
    Copyright 2018 Robin A. Richardson, David W. Wright
    This file is part of EasyVVUQ
    EasyVVUQ is free software: you can redistribute it and/or modify
    it under the terms of the Lesser GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    EasyVVUQ is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    Lesser GNU General Public License for more details.
    You should have received a copy of the Lesser GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
__license__ = "LGPL"


def encode(params):
    db_type = params[1]
    db_location = params[2]
    write_to_db = params[3]
    campaign_name = params[4]
    app_name = params[5]
    run_id_list = params[6].split(',')

    if write_to_db == 'TRUE':
        write_to_db_bool = True
    elif write_to_db == 'FALSE':
        write_to_db_bool = False
    else:
        sys.exit("write_to_db arg must be TRUE or FALSE")

    worker = uq.Worker(
        db_type=db_type,
        db_location=db_location,
        campaign_name=campaign_name,
        app_name=app_name,
        write_to_db=write_to_db_bool)

    worker.encode_runs(run_id_list)


if __name__ == "__main__":

    if 'ENCODER_MODULES' in os.environ:
        enc_modules = os.environ['ENCODER_MODULES'].split(';')
        for m in enc_modules:
            m = m.rstrip()
            print("Importing encoder module: ", m)
            module = importlib.import_module(m)

            globals().update(
                {n: getattr(module, n) for n in module.__all__} if hasattr(module, '__all__')
                else
                {k: v for (k, v) in module.__dict__.items() if not k.startswith('_')
                 })

    if len(sys.argv) != 7:
        sys.exit(
            (f"Usage: python3 external_encoder.py db_type db_location "
             "write_to_db{'TRUE' or 'FALSE'} campaign_name app_name comma_separated_run_id_list")
        )

    encode(sys.argv)
