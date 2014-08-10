"""
    %prog [options] run-name
"""
from __future__ import print_function
import sys, os
from optparse import OptionParser
import desdb
import fitsio
import eyeballer

parser=OptionParser(__doc__)

class SqliteMaker(object):
    """
    Make an sqlite db representing the files
    """
    def __init__(self, run):
        self.run=run

        conf=eyeballer.files.read_config(self.run)

        self.conf=conf
        self.run_explist=eyeballer.files.load_run_explist(conf['run_explist'])


        self.files_table='files'
        self.files_index_fields=['ccdname','expname','ccd','band']
        self.qa_table='qa'
        self.qa_index_fields=['userid','fileid','score','comments']

        self._open_connection()
        os.chdir(self.dir)

    def go(self):
        """
        Create the database and tables
        """
        self.make_files_table()
        self.populate_files_table()

        self.add_indices(self.files_table, self.files_index_fields)
    
    def add_indices(self, tablename, index_fields):
        """
        Add indexes to the table
        """
        curs=self.conn.cursor()


        for field in index_fields:
            idname='%s_%s_idx' % (tablename, field)
            query="CREATE INDEX {idname} ON {tablename} ({field})"
            query=query.format(idname=idname,
                               tablename=tablename,
                               field=field)
            print(query)
            curs.execute(query)

        curs.close()
        self.conn.commit()

    def populate_files_table(self):
        """
        Fill the file paths and meta in the table
        """

        print('populating files table')

        insert_query="""
        INSERT INTO {tablename} VALUES (?, ?, ?, ?, ?, ?)
        """.format(tablename=self.files_table)

        skip_ccds=desdb.files.SKIP_CCDS

        curs=self.conn.cursor()

        nmissing=0
        ntot=len(self.run_explist)*(62 - len(skip_ccds))
        itot=-1
        for r in self.run_explist:
            for ccd in xrange(1,62+1):
                if ccd in skip_ccds:
                    continue

                itot += 1

                fzfile=eyeballer.files.get_output_file(self.run,r['expname'],ccd)
                if not os.path.exists(fzfile):
                    print("error: missing file:",fzfile)
                    nmissing += 1
                    continue

                if (itot % 100) == 0:
                    print('    %d/%d %s' % (itot+1,ntot,fzfile))

                ccdname='%s_%02i' % (r['expname'], ccd)
                data=(r['run'],r['expname'], ccdname, ccd, r['band'], fzfile)

                curs.execute(insert_query, data)

        curs.close()
        self.conn.commit()

        print('%d/%d were missing' % (nmissing, ntot))

    def make_files_table(self):
        curs=self.conn.cursor()

        q="""
create table {tablename} (
    run text,
    expname text,
    ccdname text,
    ccd integer,
    band text,
    field text
)
        """.format(tablename=self.files_table)

        print(q)
        curs.execute(q)
        curs.close()
        self.conn.commit()

    def make_qa_table(self):
        curs=self.conn.cursor()

        q="""
create table {tablename} (
    userid int,
    fileid int,
    score int,
    comments text
)
        """.format(tablename=self.qa_table)

        print(q)
        curs.execute(q)

        curs.close()
        self.conn.commit()

    def _open_connection(self):
        import sqlite3 as sqlite
        self.url=eyeballer.files.get_db_file(self.run)
        self.dir=eyeballer.files.get_db_dir(self.run)

        if not os.path.exists(self.dir):
            os.makedirs(self.dir)

        if os.path.exists(self.url):
            print('removing existing:',self.url)
            os.remove(self.url)
        
        print('opening database:',self.url)
        self.conn=sqlite.Connection(self.url)


def main():
    options, args = parser.parse_args(sys.argv[1:])

    if len(args) != 1:
        parser.print_help()
        sys.exit(1)

    eye_run=args[0]

    maker=SqliteMaker(eye_run)
    maker.go()

main()
