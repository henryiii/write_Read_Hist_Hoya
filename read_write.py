from typing import Dict
import hist
from hist import Hist, axis



#Writing the yoda format
class Hist:
    def __init__(self, title: str, data: list):
        self.title = title
        self.data = data


def to_yoda_1d(input: Dict[str, Hist]) -> str:
    res = ""
    for path, h in input.items():
        if isinstance(h, Hist):
            res += _to_single_yoda_1d(path, h) + "\n\n"

    return res


def to_yoda_2d(input: Dict[str, Hist]) -> str:
    res = ""
    for path, h in input.items():
        if isinstance(h, Hist):
            res += _to_single_yoda_2d(path, h) + "\n\n"

    return res


def _to_single_yoda_1d(path: str, h: Hist) -> str:
    res = "BEGIN YODA_HISTO1D_V2 " + path + "\n"
    res += "Path: " + path + "\n"
    res += "Title: " + h.title + "\n"
    res += "Type: Histo1D\n"
    res += "some: stuff\n"

    # Add histogram data
    res += "---\n"

    # Calculate area and mean
    area = sum(h.data)
    mean = sum(i * value for i, value in enumerate(h.data)) / area

    # Add area and mean to YODA string
    res += f"# Mean: {mean:.6e}\n"
    res += f"# Area: {area:.6e}\n"

    res += "# ID\tID\tsumw\tsumw2\tsumwx\tsumwx2\tnumEntries\n"
    res += f"Total\tTotal\t{area:.6e}\t{area:.6e}\t{mean:.6e}\t{mean:.6e}\t{len(h.data)}\n"
    res += "Underflow\tUnderflow\t0.000000e+00\t0.000000e+00\t0.000000e+00\t0.000000e+00\t0.000000e+00\n"
    res += "Overflow\tOverflow\t0.000000e+00\t0.000000e+00\t0.000000e+00\t0.000000e+00\t0.000000e+00\n"

    res += "# xlow\txhigh\tsumw\tsumw2\tsumwx\tsumwx2\tnumEntries\n"

    # Add histogram bins
    bin_edges = [i+1 for i in range(len(h.data) + 1)]
    for xlow, xhigh, value in zip(bin_edges[:-1], bin_edges[1:], h.data):
        res += f"{xlow:.6e}\t{xhigh:.6e}\t{value:.6e}\t{value:.6e}\t{(xlow + xhigh) * 0.5 * value:.6e}\t{(xlow + xhigh) * 0.5 * value ** 2:.6e}\t{value:.6e}\n"

    res += "END YODA_HISTO1D_V2\n"
    return res


def _to_single_yoda_2d(path: str, h: Hist) -> str:
    res = "BEGIN YODA_HISTO2D_V2 " + path + "\n"
    res += "Path: " + path + "\n"
    res += "Title: " + h.title + "\n"
    res += "Type: Histo2D\n"
    res += "some: stuff\n"

    # Add histogram data
    res += "---\n"
    
    # Calculate mean and volume
    mean_x = sum(x * value for x, row in enumerate(h.data) for value in row) / sum(value for row in h.data for value in row)
    mean_y = sum(y * value for row in h.data for y, value in enumerate(row)) / sum(sum(row) for row in h.data)
    volume = sum(sum(row) for row in h.data)

    # Add mean, volume, and ID to YODA string
    res += f"# Mean: ({mean_x:.6e}, {mean_y:.6e})\n"
    res += f"# Volume: {volume:.6e}\n"
    res += "# ID\tID\tsumw\tsumw2\tsumwx\tsumwx2\tsumwy\tsumwy2\tsumwxy\tnumEntries\n"
    res += f"Total\tTotal\t{volume:.6e}\t{volume:.6e}\t{mean_x * volume:.6e}\t{mean_x * volume:.6e}\t{mean_y * volume:.6e}\t{mean_y * volume:.6e}\t0.0\t{sum(value != 0 for row in h.data for value in row)}\n"
    res += "# xlow\txhigh\tylow\tyhigh\tsumw\tsumw2\tsumwx\tsumwx2\tsumwy\tsumwy2\tsumwxy\tnumEntries\n"

    # Add histogram bins
    num_rows = len(h.data)
    num_cols = len(h.data[0])
    x_bin_edges = [i for i in range(num_rows + 1)]
    y_bin_edges = [j for j in range(num_cols + 1)]

    for i in range(num_rows):
        for j in range(num_cols):
            xlow = x_bin_edges[i]
            xhigh = x_bin_edges[i + 1]
            ylow = y_bin_edges[j]
            yhigh = y_bin_edges[j + 1]
            sumw = h.data[i][j]
            sumw2 = sumw * sumw
            sumwx = sumw * (xlow + xhigh) * 0.5
            sumwx2 = sumw * (xlow + xhigh) * 0.5 * (xlow + xhigh) * 0.5
            sumwy = sumw * (ylow + yhigh) * 0.5
            sumwy2 = sumw * (ylow + yhigh) * 0.5 * (ylow + yhigh) * 0.5
            sumwxy = sumw * (xlow + xhigh) * 0.5 * (ylow + yhigh) * 0.5
            numEntries = sum(h.data[i][j] != 0 for j in range(num_cols))
            res += f"{xlow:.6e}\t{xhigh:.6e}\t{ylow:.6e}\t{yhigh:.6e}\t{sumw:.6e}\t{sumw2:.6e}\t{sumwx:.6e}\t{sumwx2:.6e}\t{sumwy:.6e}\t{sumwy2:.6e}\t{sumwxy:.6e}\t{numEntries}\n"

    res += "END YODA_HISTO2D_V2\n"
    return res



# Reading the yoda format
def read_yoda(input) -> Dict[str, tuple[str, str]]:
    yoda_dict = {}
    lines = input.split("\n")
    num_lines = len(lines)
    i = 0
    while i < num_lines:
        line = lines[i]

        if line.startswith("BEGIN"):
            path = line.split()[2]
            class_name = line.split()[1][:-3]

            body = line + "\n"  # to include the "BEGIN" line
            i += 1
            while i < num_lines and not lines[i].startswith("END"):
                body += lines[i] + "\n"
                i += 1

            body += lines[i] + "\n"  # to include the "END" line
            yoda_dict[path] = (class_name, body)
            return body

        i += 1

    return yoda_dict


# --------------------------------------------------------------------------------
# Sample input data for 1D
h1d = {
    "/some_h1d": Hist("Histogram 1D", [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
}

# Convert to YODA string for 1D histogram
yoda_file1D = to_yoda_1d(h1d)

# Read YODA
yoda_data = read_yoda(yoda_file1D)
print(yoda_data)

# --------------------------------------------------------------------------------
# Sample input data for 2D
h2d = {
    "/some_h2d": Hist("Histogram 2D", [
        [1.0, 2.0, 3.0, 4.0, 5.0],
        [1.0, 2.0, 3.0, 4.0, 5.0],
        [1.0, 2.0, 3.0, 4.0, 5.0],
        [1.0, 2.0, 3.0, 4.0, 5.0],
        [1.0, 2.0, 3.0, 4.0, 5.0]
       ])
}

# Convert to YODA string for 2D histogram
yoda_file2D = to_yoda_2d(h2d)

# Read YODA
yoda_data2D = read_yoda(yoda_file2D)
print(yoda_data2D)


with open("file1d.yoda", "w") as file:
    file.write(yoda_file1D)
with open("file2d.yoda", "w") as file:
    file.write(yoda_file2D)