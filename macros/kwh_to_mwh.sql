{% macro kwh_to_mwh(expression) -%}
    ({{ expression }} / 1000.0)
{%- endmacro %}
