import time
import logging
import universalclient


class Tester():

    """
    Parsers the file and adds to the current phone data deltas or full file
    """

    def __init__(self, file):
        """
        sets the data and open the file for parsing

        :param str file: file path to be processed
        :return: None
        """

        logging.info('Starting fileparse')

        try:
            self.number_of_lines = self.bufcount(file)
            print('%s has %s lines' % (file, number_of_lines))
            self.cli = universalclient.Client('http://internal-lbi-abr-prod-589612350.sa-east-1.elb.amazonaws.com/search')
            self.file_for_read = open(file, encoding='UTF-8')
            self.lazy = dict()
            self.sfile = open('result.txt', 'w')

            self.readLines()
        except Exception as e:
            print('File Error: %s' % e)
            exit()

    # functions for converting input fields to usable data

    def bufcount(self, filename):
        """
        open the file 1M at a time
        """
        f = open(filename)
        lines = 0
        buf_size = 1024 * 1024
        read_f = f.read
        buf = read_f(buf_size)
        while buf:
            lines += buf.count('\n')
            buf = read_f(buf_size)

        return lines

    def readLines(self):
        """
        line reader and spliter for csv file
        """
        line = self.file_for_read.readline()

        while line:
            try:
                if len(line) > 3:
                    line = line.rstrip()
                    print(line)
                    # cli = universalclient.Client('http://internal-lbi-abr-prod-589612350.sa-east-1.elb.amazonaws.com/search')
                    # time.sleep(0.2)
                    data = self.cli._(line).get()
                    if data.status_code != 200:
                        raise Exception(data.status_code)

                    dictdata = data.json()
                    if 'error' in dictdata.keys():
                        self.sfile.write("{},{},None\n".format(line, 'Not Found'))
                    else:
                        self.sfile.write("{},{},{}\n".format(line, dictdata['operadora'], dictdata['portado']))

                    # self.sfile.flush()

            except Exception as e:
                self.sfile.write('Invalid: %s. %s\n' % (line, e))
            finally:
                line = self.file_for_read.readline()


if __name__ == '__main__':
    start_time = time.time()
    gg = Tester('./data/tt.txt')
    print("--- %s seconds ---" % (time.time() - start_time))
