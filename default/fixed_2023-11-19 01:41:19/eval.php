<?php

require_once('../_helpers/strip.php');

if (isset($_GET['variable']) && is_string($_GET['variable'])) {
    $variable = $_GET['variable'];
    $whitelist = ['allowed_variable_1', 'allowed_variable_2']; // Define your whitelist of allowed variables here
    if (in_array($variable, $whitelist)) {
        eval('echo $' . $variable . ';');
    } else {
        echo 'No variable given or invalid variable name.';
    }
} else {
    echo 'No variable given.';
}

