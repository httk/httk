// Based on https://stackoverflow.com/a/72308579 by rootShiv

function setup_pagination(table) {
    var filter = $("#filter").val().toLowerCase();
    var lastPage = 1;
    $("#maxRows").on("change", function (evt) {
        lastPage = 1;
        $(".pagination").find("li").slice(1, -1).remove();
        var trnum = 0;
        var maxRows = parseInt($(this).val());
        $(table + " tr").each(function (el) {
            a = $(this);
            txtValue = a.text().toLowerCase();
            if (!filter || txtValue.indexOf(filter) > -1) {
                trnum++;
            }
        });
        var pagenum = Math.ceil(trnum / maxRows);
        for (var i = 1; i <= pagenum; i++) {
            $(".pagination #insert-pages-here")
                .before(
                    '<li class="page-item" data-page="'+i+'"><a class="page-link" href="#">'+(i)+
                        '<span class="sr-only">(current)</span></a></li>')
                .show();
        }
        $('.pagination [data-page="1"]').addClass("active");
        $(".pagination li").on("click", function (evt) {
            evt.stopImmediatePropagation();
            evt.preventDefault();
            var pageNum = $(this).attr("data-page");
            activate_page(pageNum, table, filter);
        });
        pagination_limits();
    }).val(10).change();
    activate_page(1, table, filter);
}

function activate_page(pageNum, table, filter) {
    var maxRows = parseInt($("#maxRows").val());
    if (pageNum == "prev") {
        if (lastPage == 1) {
            return;
        }
        pageNum = --lastPage;
    }
    if (pageNum == "next") {
        if (lastPage == $(".pagination li").length - 2) {
            return;
        }
        pageNum = ++lastPage;
    }
    lastPage = pageNum;
    var trIndex = 0;
    $(".pagination li").removeClass("active");
    $('.pagination [data-page="' + lastPage + '"]').addClass("active");
    pagination_limits();
    $(table + " tr").each(function () {

        a = $(this);
        txtValue = a.text().toLowerCase();
        if (!filter || txtValue.indexOf(filter) > -1) {
            trIndex++;
            if (trIndex > maxRows * pageNum || trIndex <= maxRows * pageNum - maxRows) {
                $(this).hide();
            } else {
                $(this).show();
            }
        } else {
            $(this).hide();
        }
    });
}

function pagination_limits() {
  if ($(".pagination li").length > 7) {
    if ($(".pagination li.active").attr("data-page") <= 3) {
      $(".pagination li:gt(5)").hide();
      $(".pagination li:lt(5)").show();
      $('.pagination [data-page="next"]').show();
    }
    if ($(".pagination li.active").attr("data-page") > 3) {
      $(".pagination li:gt(0)").hide();
      $('.pagination [data-page="next"]').show();
      for (
        let i = parseInt($(".pagination li.active").attr("data-page")) - 2;
        i <= parseInt($(".pagination li.active").attr("data-page")) + 2;
        i++
      ) {
        $('.pagination [data-page="' + i + '"]').show();
      }
    }
  }
}

$('#filterform').on('reset', function(e)
{
   setTimeout(function() { setup_pagination("#table-id"); });
});

$('#filterform').on('submit',function(event) {
    event.preventDefault();
});

setup_pagination("#table-id");
