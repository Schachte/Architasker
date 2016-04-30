jQuery(document).ready(function(){
    jQuery('#hideshowcurremail').on('click', function(event) {
         jQuery('#currentemail').toggle(500);
    });
    jQuery('#hideshowcurrtz').on('click', function(event) {
         jQuery('#currenttz').toggle(500);
    });
    jQuery('#tzDrop').on('click', function(event) {
         jQuery('#tzDropdown').toggle(500);
    });
});

$("#savename").submit(function(event) {

    /* stop form from submitting normally */
    event.preventDefault();

    /* get some values from elements on the page: */
    var $form = $( this ),
        url = $form.attr( 'action' );

    /* Send the data using post */
    $.ajax({
        type: "POST",
        url: url,
        datatype: "json",
        data: {
            csrfmiddlewaretoken: '{{ csrf_token }}',
            first_name: $('#firstname').val(),
            last_name: $('#lastname').val(),
        },
        success: function(){
            jQuery('#namesuccess').show();
            setTimeout(function(){
                $("#namesuccess").fadeOut("slow", function () {
                });

            }, 3000);
        },
    });
});

$("#savepass").submit(function(event) {

    /* stop form from submitting normally */
    event.preventDefault();

    /* get some values from elements on the page: */
    var $form = $( this ),
        url = $form.attr( 'action' );

    /* Send the data using post */
    $.ajax({
        type: "POST",
        url: url,
        datatype: "json",
        data: {
            csrfmiddlewaretoken: '{{ csrf_token }}',
            old_pass: $('#oldpass').val(),
            new_pass: $('#newpass').val(),
            new_pass2: $('#newpass2').val(),
        },
        success: function(){
            jQuery('#passsuccess').show();
            setTimeout(function(){
                $("#passsuccess").fadeOut("slow", function () {
                });

            }, 3000);
        },
    });
});

$("#saveemail").submit(function(event) {

    /* stop form from submitting normally */
    event.preventDefault();

    /* get some values from elements on the page: */
    var $form = $( this ),
        url = $form.attr( 'action' );

    /* Send the data using post */
    $.ajax({
        type: "POST",
        url: url,
        datatype: "json",
        data: {
            csrfmiddlewaretoken: '{{ csrf_token }}',
            email: $('#email').val(),
        },
        success: function(){
            $('#currentemail').text($('#email').val());
            jQuery('#emailsuccess').show();
            setTimeout(function(){
                $("#emailsuccess").fadeOut("slow", function () {
                });

            }, 3000);
        },
    });
});

$("#savetz").submit(function(event) {

    /* stop form from submitting normally */
    event.preventDefault();

    /* get some values from elements on the page: */
    var $form = $( this ),
        url = $form.attr( 'action' );

    /* Send the data using post */
    $.ajax({
        type: "POST",
        url: url,
        datatype: "json",
        data: {
            csrfmiddlewaretoken: '{{ csrf_token }}',
            tz: selected_zone,
        },
        success: function(){
            jQuery('#currenttz').hide(500);
            jQuery('#tzDropdown').hide(500);
            $li.removeClass('selected');
            $('#currenttz').text(selected_zone);
            jQuery('#tzsuccess').show();
            setTimeout(function(){
                $("#tzsuccess").fadeOut("slow", function () {
                });

            }, 3000);
        },
    });
});

var $li = $('#tzDropdown li').click(function() {
    selected_zone = $(this).text();
    $li.removeClass('selected');
    $(this).addClass('selected');
});