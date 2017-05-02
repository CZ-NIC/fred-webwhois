/*
    Webwhois and Public requests
*/

(function ($) {

    $(document).ready(function() {
        $("input[name=send_to]").click(function() {
            if ($(this).val() == "email_in_registry") {
                $("input[name=custom_email]").val("").prop('disabled', true).removeClass("required");
                $("select[name=confirmation_method]").val("signed_email").prop('disabled', true);
            } else {
                $("input[name=custom_email]").prop('disabled', false).addClass("required");
                $("select[name=confirmation_method]").prop('disabled', false);
            }
        });
        if ($("input[name=send_to]:checked").val() == "email_in_registry") {
            $("input[name=custom_email]").val("").prop('disabled', true).removeClass("required");
            $("select[name=confirmation_method]").prop('disabled', true);
        } else {
            $("input[name=custom_email]").prop('disabled', false).addClass("required");
        }

        $("select[name=confirmation_method]").change(function () {
            if ($(this).val() == "notarized_letter") {
                $("input[name=send_to][value=custom_email]").prop('checked', true);
                $("input[name=custom_email]").prop('disabled', false).addClass("required");
            }
        });

        $("input[name=handle]").addClass("required");
        $("form.webwhois-send-password, form.webwhois-block-object, form.webwhois-unblock-object").submit(function () {
            $("ul.errorlist").remove();
            $("input.required").each(function () {
                if(!$(this).val()) {
                    var message;
                    try {
                        message = gettext("This field is required.");
                    } catch(err) {
                        console.log(err);
                        message = "This field is required.";
                    }
                    $(this).before("<ul class='errorlist'><li>" + message + "</li></ul>");
                }
            });
            return !$("ul.errorlist").length;
        });

    });

}(django.jQuery));
