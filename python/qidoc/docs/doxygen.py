import os

import qisys
import qidoc.templates

from qidoc.docs.documentation import Documentation, ConfigureFailedError

class DoxygenDoc(Documentation):
    '''This class configures and build a project of type doxygen.'''

    def type_name(self):
        return 'doxygen'

    def get_mapping(self, docs, **kwargs):
        res = dict()
        for dep_name in self.dependencies:
            dep = docs[dep_name]
            doxytag_file = os.path.join(kwargs['doxytags_path'],
                                        dep.name + ".tag")
            res[doxytag_file] = (os.path.realpath(dep.dest), self.dest)
        return res

    def _configure(self, docs, opts, **kwargs):
        try:
            templates = kwargs['templates']
            doxytags_path = kwargs['doxytags_path']
        except KeyError as err:
            raise ConfigureFailedError(self.name,
                'Keyword argument `{opt}` is missing'.format(opt = err)
            )
        for name in ['Doxyfile.in', 'header.in.html', 'footer.in.html']:
            if name == 'Doxyfile.in':
                out_name = 'Doxyfile.qidoc'
            else:
                out_name = name.replace('.in.', '.')
            out_file = os.path.join(self.src, out_name)
            in_file  = os.path.join(templates, 'doxygen', name)
            opts['PROJECT_NAME'] = self.name
            opts['PROJECT_NUMBER'] = opts['version']
            opts['OUTPUT_DIRECTORY'] = 'build-doc'
            opts['GENERATE_TAGFILE'] = ''
            opts['INTERNAL_DOCS'] = 'NO' if opts['release'] else 'YES'
            opts['QUIET'] = 'NO' if opts['verbose'] else 'YES'
            if doxytags_path:
                tag_file = os.path.join(doxytags_path, self.name + '.tag')
                opts['GENERATE_TAGFILE'] = tag_file

            # tag files for dependencies.
            tagfiles, doxygen_mapping = list(), self.get_mapping(docs, **kwargs)
            if doxygen_mapping:
                for (key, value) in doxygen_mapping.iteritems():
                    rel_path = os.path.relpath(value[0], self.dest)
                    tagfiles.append("%s=%s" % (key, rel_path))
            opts["TAGFILES"] = " ".join(tagfiles)

            append_file = None
            if name == "Doxyfile.in":
                append_file = os.path.join(self.src, "Doxyfile.in")
            qidoc.templates.configure_file(in_file, out_file,
                                           append_file=append_file,
                                           opts=opts)

        tag_file = os.path.join(doxytags_path, self.name + ".tag")
        kwargs['doxylink'][self.name] = (tag_file, self.dest)

        # Also copy the css:
        qisys.sh.install(
            os.path.join(templates, "doxygen", "doxygen.css"),
            os.path.join(self.src, "doxygen.css"),
            quiet=True)

    def _build(self, docs, opts, **kwargs):
        cmd = ["doxygen", "Doxyfile.qidoc"]
        qisys.command.call(cmd, cwd=self.src)
        build_html = os.path.join(self.src, "build-doc", "html")
        qisys.sh.install(build_html, self.dest, quiet=True)
