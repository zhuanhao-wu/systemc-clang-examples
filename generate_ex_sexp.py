"""generate sexp and text files in ex_* examples"""
import os
import subprocess
import re
from shutil import copy, move
from pathlib import Path

TMPDIR = './temp/'

SYSTEMC_CLANG_BIN_PATH = os.environ['LLVM_INSTALL_DIR'] + "/bin/systemc-clang"
PYTHON_CONVERT_TEMPLATE = 'python {}/{}'.format(
    os.environ['SYSTEMC_CLANG_BUILD_DIR'],
    "../systemc-clang/plugins/xlat/convert.py"
)
SYSTEMC_CLANG_ARGUMENTS = [
    "-I", "{}/include/".format(os.environ['SYSTEMC']),
    "-std=c++14",
    "-I", "/usr/include/",
    "-D__STDC_CONSTANT_MACROS",
    "-D__STDC_LIMIT_MACROS",
    "-x c++ -w -c"
]


def systemc_clang_commandline(filename, positional_arguments):
    """
    Extra args are positional and non positional arguments, for example,
    extra header etc
    """
    args = SYSTEMC_CLANG_ARGUMENTS + positional_arguments
    return [
        SYSTEMC_CLANG_BIN_PATH,
        filename,
        '--'
    ] + args + [
        # for the containing folder of the cpp/hpp
        "-I", str(Path(filename).parent)
    ]


def detect_module(directory, exid):
    """detect the module that is in each folder"""
    module_list = [
        fn for fn in os.listdir(directory)
        if fn.endswith('.cpp') or fn.endswith('.hpp')
    ]
    if not module_list:
        print('no module found for ex_{}'.format(exid))
        exit()
    elif len(module_list) > 1:
        print('more than 1 c++ file found for ex_{}'.format(exid))
        exit()
    return module_list[0]


def main():
    """drives the generation process"""
    error_list = []
    v_error_list = []

    for exid in range(1, 16):
        print(exid)

        # copy from source folder
        src_dir = '../../../examples/ex_{}/'.format(exid)
        if not os.path.isdir(src_dir):
            print('ex_{} does not exist'.format(exid))
            continue
        module_name = detect_module(src_dir, exid)
        print('detected module: ', module_name)
        target_module_name = re.sub(".hpp$", ".cpp", module_name)
        copy(src_dir + module_name, TMPDIR + '/' + target_module_name)

        # run the plugin
        cmdline = ' '.join(systemc_clang_commandline(
            TMPDIR + target_module_name,
            []
        ))
        try:
            res = subprocess.run(cmdline, shell=True)
            if res.returncode != 0:
                raise RuntimeError('Something wrong with the systemc-clang result')
            # move the generated file
            filename = re.sub(".cpp$", "_hdl.txt", target_module_name)
            ex_target_path = './ex_{}/handcrafted/{}'.format(exid, filename)
            move(
                TMPDIR + filename,
                ex_target_path
            )
        except subprocess.CalledProcessError:
            print('Some error happend for ex_{}, please check'.format(exid))
            error_list.append(exid)
            continue
        except RuntimeError as runtime_exception:
            print('Some error happend for ex_{}, '
                  'please check: {}'.format(exid, runtime_exception))
            error_list.append(exid)
            continue

        # now run the convert.py plugin
        convert_cmdline = ' '.join([
            PYTHON_CONVERT_TEMPLATE,
            os.path.abspath(ex_target_path)
        ])
        try:
            # no need to mv, done inplace
            print(convert_cmdline)
            subprocess.run(convert_cmdline, shell=True)
        except subprocess.CalledProcessError:
            print('Some error happend for ex_{}, please check'.format(exid))
            v_error_list.append(exid)

    if error_list:
        print('Some error happend for ex_{} (cpp -> sexp), '
              'please check'.format(error_list))
    if v_error_list:
        print('Some error happend for ex_{} (sexp -> verilog), '
              'please check'.format(v_error_list))


if __name__ == '__main__':
    main()
