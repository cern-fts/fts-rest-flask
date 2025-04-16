/*
 *  Copyright 2025 CERN
 *
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
**/

var template_token_provider = null;

/**
 * Handling saving Token Provider configuration (new and existing)
 */
function handleTokenProviderSave(form)
{
    form.css("background", "#3c763d").css("transition", "none");

    var provider = {};
    provider.name = form.find("input[name='name']").val();
    provider.issuer = form.find("input[name='issuer']").val();
    provider.client_id = form.find("input[name='client_id']").val();
    provider.client_secret = form.find("input[name='client_secret']").val();
    provider.required_submission_scope = form.find("input[name='required_submission_scope']").val();
    provider.vo_mapping = form.find("input[name='vo_mapping']").val();

    console.log("Adding new token provider: " + provider);

    return $.ajax({
        url: "/config/token_providers",
        type: "POST",
        dataType: "json",
        contentType: "application/json",
        data: JSON.stringify(provider)
    })
    .always(function() {
        form.css("background", "#ffffff").css("transition", "background .50s ease-in-out");
    });
}

/**
 * Delete Token Provider configuration
 */
function deleteTokenProvider(form)
{
    var name = form.find("input[name='name']").val();
    console.log("about to delete: " + name + "(" + encodeURIComponent(name)+ ")")
    form.css("background", "#ff0000").css("transition", "background .50s ease-in-out");
    $.ajax({
        url: "/config/token_providers/" + encodeURIComponent(name),
        type: "DELETE",
        dataType: "json",
        contentType: "application/json"
    })
    .done(function(data, textStatus, jqXHR) {
        form.fadeOut(300, function() {form.remove();})
    })
    .fail(function(jqXHR) {
        errorMessage(jqXHR);
    })
    .always(function() {
        form.css("background", "#ffffff").css("transition", "background .50s ease-in-out");
    });
}

/**
 * Manage the list of configured OAuth2 Token Providers
 */
function refreshTokenProvidersConfig()
{
    var parent = $("#token-providers-list");

    $.ajax({
        headers: {
            Accept : "application/json",
        },
        url: "/config/token_providers",
    })
    .done(function(data, textStatus, jqXHR) {
        parent.empty();
        $.each(data, function(index, token_provider) {
            var item = $(template_token_provider(token_provider));

            item.find("#token-provider-modify-form").submit(function(event) {
                event.preventDefault();
                handleTokenProviderSave(item)
                    .done(function(data, textStatus, jqXHR) {
                        $("#token-provider-modify-form").trigger("reset");
                        refreshTokenProvidersConfig();
                    })
                    .fail(function(jqXHR) {
                        errorMessage(jqXHR);
                    });
            });

            item.find(".btn-delete").click(function(event) {
                event.preventDefault();
                deleteTokenProvider(item);
            });

            parent.append(item);
        });
    })
    .fail(function(jqXHR) {
        errorMessage(jqXHR);
    });
}

/**
 * Add a new OAuth2 Token Provider
 */
function addTokenProviderConfig()
{
    $("#token-provider-add-form").submit(function(event) {
        event.preventDefault();
        handleTokenProviderSave($("#token-provider-add-form"))
            .done(function(data, textStatus, jqXHR) {
                $("#token-provider-add-form").trigger("reset");
                refreshTokenProvidersConfig();
            })
            .fail(function(jqXHR) {
                errorMessage(jqXHR);
            });
    });
}

/**
 * Compile templates embedded into the HTML
 */
function compileTemplates()
{
    template_token_provider = Handlebars.compile(
        $("#token-provider-template").html()
    );
}

/**
 * Initialize the TokenProvider view
 */
function setupTokenProviders()
{
    compileTemplates();
    // Display token providers list
    refreshTokenProvidersConfig();
    // Handle addition of new token provider
    addTokenProviderConfig();

}
