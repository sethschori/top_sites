function sortRows(dataAttrToSortBy) {
    /** Hat tip to https://stackoverflow.com/a/14131059 for this function.
    I adapted the SO code to the needs of top_sites, but it's based on that
    example code. **/
    var tbody = document.getElementsByTagName("tbody")[0];
    currentSort = tbody.getAttribute("data-sorted-by");
    var elems = document.getElementsByClassName('sitesRow');
    var rows = [];
    for (var i = 0; i < elems.length; i++) {
        rows.push(elems[i]);
    }
    if (currentSort.length == 0 || currentSort != dataAttrToSortBy) {
        rows.sort(function(a, b) {
            a = String(a.getAttribute(dataAttrToSortBy))
            b = String(b.getAttribute(dataAttrToSortBy))
            return a.localeCompare(b, 'en', {numeric: true})
        });
    } else {
        rows.reverse();
    }

    rows.forEach(function(el) {
        tbody.appendChild(el);
    });

    tbody.setAttribute("data-sorted-by", dataAttrToSortBy);
    currentSort = tbody.getAttribute("data-sorted-by");
}
