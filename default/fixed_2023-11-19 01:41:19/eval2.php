<?php

use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\Routing\Annotation\Route;

use Symfony\Component\HttpClient\HttpClient;
use Symfony\Component\HttpClient\HttpClientInterface;

use Symfony\Component\Form\Form;
use Symfony\Component\Form\Forms;
use Symfony\Component\Form\Extension\Core\Type\TextType;


function new_http_param() {
    $r = new Request(
        $_GET,
        $_POST,
        [],
        $_COOKIE,
        $_FILES,
        $_SERVER
    );
    // Do not use eval with user-supplied data
    // If dynamic PHP code execution is absolutely necessary (which it rarely is), use a solution
    // that does not involve `eval`, and ensure proper input validation and sandboxing.
}

?>
