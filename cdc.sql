WITH tab_orders AS (
SELECT
	O.id AS order_id
	, O.code AS order_code
	, O.token AS token
	, B.name AS bay_name
	, L.dock AS dock
	, V.name AS vehicle_name
	, L.code AS load_code
	, L.delivery_date AS delivery_date
	, PT.name AS pallet_type_name
	, L.quantity_mixed_pallets 
	, L.quantity_full_pallets 
	, L.quantity_orders 
   , (
        SELECT
            SUM(OP.quantity)
        FROM casadiconti.order_products OP
        WHERE
            OP.order_id = O.id
    ) AS boxes_quantity
	, (
		SELECT
			U."name"
		FROM casadiconti.order_histories OH
		INNER JOIN casadiconti.history_types HT ON (HT.id = OH.history_type_id)
		INNER JOIN casadiconti.users U ON (U.id = OH.user_id)
		WHERE
			HT."name" = 'Fim da Montagem'
			AND OH.order_id = O.id
		ORDER BY
			OH.id DESC
		LIMIT 1
	) AS assembler_name
	, (
		SELECT
			TO_CHAR(OH.created_at - INTERVAL '3 hour', 'YYYY-MM-DD HH24:MI:SS')
		FROM casadiconti.order_histories OH
		INNER JOIN casadiconti.history_types HT ON (HT.id = OH.history_type_id)
		WHERE
			HT."name" = 'Início da Montagem'
			AND OH.order_id = O.id
		ORDER BY
			OH.created_at
		LIMIT 1
	) AS start_assembly
	, (
		SELECT
			TO_CHAR(OH.created_at - INTERVAL '3 hour', 'YYYY-MM-DD HH24:MI:SS')
		FROM casadiconti.order_histories OH
		INNER JOIN casadiconti.history_types HT ON (HT.id = OH.history_type_id)
		WHERE
			HT."name" = 'Fim da Montagem'
			AND OH.order_id = O.id
		ORDER BY
			OH.created_at DESC
		LIMIT 1
	) AS end_assembly
	, (
		SELECT
			U."name"
		FROM casadiconti.order_histories OH
		INNER JOIN casadiconti.history_types HT ON (HT.id = OH.history_type_id)
		INNER JOIN casadiconti.users U ON (U.id = OH.user_id)
		WHERE
			HT."name" = 'Aprovação da Montagem'
			AND OH.order_id = O.id
		ORDER BY
			OH.created_at DESC
		LIMIT 1
	) AS checker_name
	, (
		SELECT
			TO_CHAR(OH.created_at - INTERVAL '3 hour', 'YYYY-MM-DD HH24:MI:SS')
		FROM casadiconti.order_histories OH
		INNER JOIN casadiconti.history_types HT ON (HT.id = OH.history_type_id)
		INNER JOIN casadiconti.order_steps OS ON (OS.id = OH.order_step_id)
		INNER JOIN casadiconti.statuses ST ON (ST.id = OS.status_id)
		WHERE
			HT."name" = 'Início da Conferência'
			AND ST."name" IN ('Conferência','Liberação de Caminhão')
			AND OH.order_id = O.id
		ORDER BY
			OH.created_at DESC
		LIMIT 1
	) AS start_check
	, (
		SELECT
			TO_CHAR(OH.created_at - INTERVAL '3 hour', 'YYYY-MM-DD HH24:MI:SS')
		FROM casadiconti.order_histories OH
		INNER JOIN casadiconti.history_types HT ON (HT.id = OH.history_type_id)
		INNER JOIN casadiconti.order_steps OS ON (OS.id = OH.order_step_id)
		INNER JOIN casadiconti.statuses ST ON (ST.id = OS.status_id)
		WHERE
			HT."name" = 'Fim da Conferência'
			AND ST."name" IN ('Conferência','Liberação de Caminhão')
			AND OH.order_id = O.id
		ORDER BY
			OH.created_at DESC 
		LIMIT 1
	) AS end_check
	, NOW() AS created_at
	, NOW() AS updated_at
	, 1 AS company_id
	, 'casadiconti#' || CAST(O.id AS TEXT) AS integration_id
	, LO."name" AS locality_name
	, L.integration_id AS trip_number
	, (
		SELECT	
			c."name" 
		FROM casadiconti.load_products lp
		INNER JOIN casadiconti.clients c ON (lp.client_id = c.id)
		INNER JOIN casadiconti.orders o2 ON (o2.load_id = lp.load_id)
		WHERE
			o2.id = o.id
		LIMIT 1
	) AS client_name
	, (
		SELECT
			TO_CHAR(OH.created_at - INTERVAL '3 hour', 'YYYY-MM-DD HH24:MI:SS')
		FROM casadiconti.order_histories OH
		INNER JOIN casadiconti.history_types HT ON (HT.id = OH.history_type_id)
		WHERE
			HT."name" = 'Empilhamento'
			AND OH.order_id = O.id
		ORDER BY
			OH.created_at DESC
		LIMIT 1
	) AS stacking_time
	, (
		SELECT
			U."name"
		FROM casadiconti.order_histories OH
		INNER JOIN casadiconti.history_types HT ON (HT.id = OH.history_type_id)
		INNER JOIN casadiconti.users U ON (U.id = OH.user_id)
		WHERE
			HT."name" = 'Empilhamento'
			AND OH.order_id = O.id
		ORDER BY
			OH.created_at DESC
		LIMIT 1
	) AS stacker_name
	, D.start_of_operation - INTERVAL '3 hour' AS start_of_operation
	, D.start_of_interval - INTERVAL '3 hour' AS start_of_interval
	, D.end_of_interval - INTERVAL '3 hour' AS end_of_interval
	, D.end_of_operation - INTERVAL '3 hour' AS end_of_operation
FROM casadiconti.orders O
INNER JOIN casadiconti.loads L ON (L.id = O.load_id)
INNER JOIN casadiconti.bays B ON (B.id = O.bay_id)
INNER JOIN casadiconti.vehicles V ON (V.id = L.vehicle_id)
INNER JOIN casadiconti.pallet_types PT ON (PT.id = O.pallet_type_id)
INNER JOIN casadiconti.localities LO ON (LO.id = L.locality_id)
INNER JOIN casadiconti.daily_operations D ON (D.id = L.daily_operation_id)
WHERE
--    L.delivery_date BETWEEN $1 AND $2
    cast(D.start_of_operation AS date) BETWEEN $1 AND $2
	AND L.assembled_percentage = 100
	AND L.checked_percentage = 100
	AND l.loaded_percentage = 100
	AND o.id != 2524
)
, tab_order_products AS (
SELECT 
	op.order_id
	, l.id AS load_id
	, p.integration_id AS product_integration_id
	, l.delivery_date
	, lc."name" AS locality_name
	, p."name" AS product_name
	, op.quantity AS quantity
	, op.box 
	, p2.weight AS unit_weight
	, (p2.weight * op.quantity) AS total_weight
	, PT.name AS pallet_type_name
	, p2."name" AS package_name
	, p2.ballast
	, p2.full_pallet 
	, F."name" AS fragility_name
	, V."name" AS vehicle_name
	, VT."name" AS vehicle_type_name	
	, l.integration_id AS trip_number
	, 'casadiconti#' || CAST(L.integration_id AS TEXT) || '#' || CAST(OP.id AS TEXT) AS integration_id
	, NOW() AS created_at
	, NOW() AS updated_at
FROM casadiconti.order_products op
LEFT JOIN casadiconti.orders o ON (o.id = op.order_id)
LEFT JOIN casadiconti.loads l ON (l.id = o.load_id)
LEFT JOIN casadiconti.products p ON (p.id = op.product_id)
LEFT JOIN casadiconti.packages p2 ON (p2.id = p.package_id)
LEFT JOIN casadiconti.localities lc ON (lc.id = l.locality_id)
LEFT JOIN casadiconti.pallet_types PT ON (PT.id = O.pallet_type_id)
LEFT JOIN casadiconti.vehicles V ON (V.id = L.vehicle_id)
LEFT JOIN casadiconti.vehicle_types VT ON (VT.id = V.vehicle_type_id)
LEFT JOIN casadiconti.fragilities F ON (F.id = P.fragility_id)
WHERE
--    L.delivery_date  BETWEEN $1 AND $2
	L.assembled_percentage = 100
	AND L.checked_percentage = 100
	AND l.loaded_percentage = 100
)
--
-- ###############################  tabela tab_orders.csv
--select
--    locality_name as "UNIDADE"
--    , delivery_date as "DATA_ENTREGA"
--    , client_name AS "CLIENTE"
--    , load_code AS "CODIGO_CARGA"
--    , trip_number AS "TRANSPORTE"
--    , quantity_orders AS "TOTAL_PALETES"
--	, quantity_mixed_pallets AS "TOTAL_PALETES_MISTOS"
--	, quantity_full_pallets AS "TOTAL_PALETES_COMPLETOS"
--    , vehicle_name AS "VEICULO"   
--    , order_code as "LISTA"
--    , boxes_quantity AS "CAIXAS"
--    , pallet_type_name AS "TIPO_PALETE"
--    , token AS "TOKEN"
--    , bay_name AS "BAIA"
--    , dock AS "DOCA"
--    , assembler_name AS "MONTADOR"
--    , start_assembly AS "INICIO_MONTAGEM"
--    , end_assembly AS "FIM_MONTAGEM"
--    , ROUND(CAST((EXTRACT(EPOCH FROM (end_assembly::timestamp - start_assembly::timestamp))) AS NUMERIC)/60, 2) AS "TEMPO_MONTAGEM"
--    , checker_name AS "CONFERENTE"
--    , start_check AS "INICIO_CONFERENCIA"
--    , end_check AS "FIM_CONFERENCIA"
--    , stacker_name AS "EMPILHADOR"
--    , stacking_time AS "HORARIO_EMPILHAMENTO"
--    , start_of_operation AS "INICIO_OPERACAO"
--    , end_of_operation AS "FIM_OPERACAO"
--from tab_orders
-- 
-- ####################### tabela caixa_hora.csv
--, tab as (
--    SELECT 
--        assembler_name, 
--        delivery_date, 
--        end_assembly, 
--        start_assembly, 
--        boxes_quantity,
--        CASE 
--            WHEN EXTRACT(day FROM end_assembly::timestamp) - EXTRACT (day FROM start_assembly::timestamp) = 0 THEN SUM(CAST((EXTRACT(hour FROM end_assembly::timestamp)*3600 + EXTRACT(minute FROM end_assembly::timestamp)*60 + EXTRACT(second FROM end_assembly::timestamp))/3600 AS DECIMAL)
--                - CAST((EXTRACT(hour FROM start_assembly::timestamp)*3600 + EXTRACT(minute FROM start_assembly::timestamp)*60 + EXTRACT(second FROM start_assembly::timestamp))/3600 AS DECIMAL))
--            ELSE SUM(24 + (CAST((EXTRACT(hour FROM end_assembly::timestamp)*3600 + EXTRACT(minute FROM end_assembly::timestamp)*60 + EXTRACT(second FROM end_assembly::timestamp))/3600 AS DECIMAL)
--                - CAST((EXTRACT(hour FROM start_assembly::timestamp)*3600 + EXTRACT(minute FROM start_assembly::timestamp)*60 + EXTRACT(second FROM start_assembly::timestamp))/3600 AS DECIMAL)))
--        END AS hrs
--    FROM tab_orders
--    WHERE
--        pallet_type_name <> 'COMPLETO'
--        AND assembler_name IS NOT NULL
--    GROUP BY
--        delivery_date, assembler_name, end_assembly, start_assembly, boxes_quantity
--)
--SELECT 
--    assembler_name AS "MONTADOR"
--    , delivery_date AS "DATA_ENTREGA"
--    , sum(boxes_quantity)/sum(hrs) AS "CAIXA_HORA"
--FROM tab
--GROUP BY 
--	assembler_name, delivery_date 
--HAVING	
--	sum(boxes_quantity)/sum(hrs) < 1000
---
-- ########################################### tabela media_conf_dia.csv
--SELECT
--	T.conferente
--	, TO_CHAR((avg(tempo_conferencia)|| 'hour')::interval, 'HH24:MI:SS') as tempo_medio_conferencia
--	, (avg(tempo_conferencia)|| 'hour')::INTERVAL AS tempo
--	, data_entrega
--FROM (
--	SELECT 
--		checker_name AS conferente
--		, delivery_date AS data_entrega
--        , (end_check::timestamp - start_check::timestamp) as tempo_conferencia
--	FROM tab_orders
--	WHERE
--		checker_name IS NOT NULL
--		AND end_check::timestamp - start_check::timestamp > '0'
--        AND end_check IS NOT NULL
--        AND start_check IS NOT NULL
--) AS T
--GROUP BY 
--	data_entrega, T.conferente
--	
-- #################################### tabela conf_registros.csv
--SELECT 
--	checker_name AS conferente
--	, delivery_date AS data_entrega
--	, boxes_quantity AS caixas
--    , (end_check::timestamp - start_check::timestamp) as tempo_conferencia
--FROM tab_orders
--WHERE
--	checker_name IS NOT NULL
--	AND end_check::timestamp - start_check::timestamp > '0'
--    AND end_check IS NOT NULL
--    AND start_check IS NOT NULL
----
-- #################### tabela montagem_transporte.csv
--, tab_tempo AS (
--select
--    trip_number AS "TRANSPORTE"
--    , delivery_date AS "DATA_ENTREGA"
--    , quantity_mixed_pallets AS "TOTAL_PALETES_MISTOS"
--    , order_code as "LISTA"
--    , assembler_name AS "MONTADOR"    
--    , boxes_quantity AS "CAIXAS"
--	, end_assembly::timestamp - start_assembly::timestamp AS "TEMPO_MONTAGEM_POR_USUARIO"
--from tab_orders
--WHERE	
--	pallet_type_name = 'MISTO'
--)
--, tab_transp AS (
--SELECT 
--	"TRANSPORTE"
--	, sum("TEMPO_MONTAGEM_POR_USUARIO") AS "TEMPO_MONTAGEM_POR_TRANSPORTE"
--FROM tab_tempo
--GROUP BY 
--	"TRANSPORTE"
--)
--SELECT 
--	*
--FROM tab_tempo 
--LEFT JOIN tab_transp ON (tab_transp."TRANSPORTE" = tab_tempo."TRANSPORTE")
----
-- ############################# tabela tempo_medio_mont.csv
--SELECT
--	T.data_entrega
--	, T.montador
--    , ROUND(CAST(AVG(T.tempo_montagem) AS NUMERIC), 2) AS tempo_medio_montagem
--    , avg(tempo_hor) AS tempo_med_format
--FROM (
--	SELECT 
--		assembler_name AS montador
--		, delivery_date AS data_entrega
--		, CASE 
--			WHEN ROUND(CAST((EXTRACT(EPOCH FROM (end_assembly::timestamp - start_assembly::timestamp))) AS NUMERIC)/60, 2) <= 0 THEN 1
--			WHEN ROUND(CAST((EXTRACT(EPOCH FROM (end_assembly::timestamp - start_assembly::timestamp))) AS NUMERIC)/60, 2) IS NULL THEN 1
--		ELSE
--			ROUND(CAST((EXTRACT(EPOCH FROM (end_assembly::timestamp - start_assembly::timestamp))) AS NUMERIC)/60, 2)
--		END AS tempo_montagem
--		, end_assembly::timestamp - start_assembly::timestamp AS tempo_hor
--	FROM tab_orders
--	WHERE
--		assembler_name IS NOT NULL
--		AND pallet_type_name IN ('MISTO', 'CONTAINER', 'LP DUPLO', 'GAVETA', 'RETORNAVEL')
--) AS T
--GROUP BY 
--	T.data_entrega, T.montador
--
-- ############################# tabela tab_duracao_operacao.csv
--, tab_op AS (
--	SELECT 
--		d.id 
--		, (
--			SELECT 
--				lh.created_at - INTERVAL '3 hour'
--			FROM load_histories lh 
--			LEFT JOIN loads l ON (lh.load_id = l.id)
--			LEFT JOIN history_types ht ON (lh.history_type_id = ht.id)
--			LEFT JOIN daily_operations t ON (l.daily_operation_id = t.id)
--			WHERE 
--				t.id = d.id
--				AND ht."name" = 'Paletização'
--			ORDER BY 
--				lh.created_at ASC
--			LIMIT 1
--		) AS "INÍCIO DA OPERAÇÃO"
--		, d.start_of_interval - INTERVAL '3 hour' AS "INÍCIO DO INTERVALO"
--		, d.end_of_interval - INTERVAL '3 hour' AS "FIM DO INTERVALO"
--		, d.end_of_operation - INTERVAL '3 hour' AS end_of_operation
--		, (
--			SELECT 
--				lh.created_at - INTERVAL '3 hour'
--			FROM load_histories lh 
--			LEFT JOIN loads l ON (lh.load_id = l.id)
--			LEFT JOIN history_types ht ON (lh.history_type_id = ht.id)
--			LEFT JOIN daily_operations t ON (l.daily_operation_id = t.id)
--			WHERE 
--				t.id = d.id
--				AND ht."name" = 'Fim do Carregamento'
--			ORDER BY 
--				lh.created_at DESC
--			LIMIT 1
--		) AS "FIM DA OPERAÇÃO"
--		, (
--			SELECT
--				oh.created_at - INTERVAL '3 hour'
--			FROM order_histories oh 
--			LEFT JOIN orders o ON (oh.order_id = o.id)
--			LEFT JOIN loads l ON (o.load_id = l.id)
--			LEFT JOIN history_types ht ON (oh.history_type_id = ht.id)
--			LEFT JOIN daily_operations t ON (l.daily_operation_id = t.id)
--			WHERE 
--				ht."name" = 'Empilhamento'
--				AND t.id = d.id
--			ORDER BY 
--				oh.created_at DESC
--			LIMIT 1		
--		) AS "ULTIMO EMPILHAMENTO"
--	FROM daily_operations d
--	WHERE 
--	    cast(D.start_of_operation AS date) BETWEEN $1 AND $2
--)
--, tab_calc AS (
--	SELECT 
--		id
--		, "INÍCIO DA OPERAÇÃO"
--		, "INÍCIO DO INTERVALO"
--		, "FIM DO INTERVALO" 
--		, "FIM DA OPERAÇÃO"
--		, end_of_operation
--		, "ULTIMO EMPILHAMENTO"
--	    , case 
--	        when ("INÍCIO DO INTERVALO" is null or "FIM DO INTERVALO" is null) 
--	            then TO_CHAR((("FIM DA OPERAÇÃO" - "INÍCIO DA OPERAÇÃO")|| 'hour')::interval, 'HH24:MI:SS') 
--	        else TO_CHAR((("FIM DA OPERAÇÃO" - "FIM DO INTERVALO" + ("INÍCIO DO INTERVALO" - "INÍCIO DA OPERAÇÃO"))|| 'hour')::interval, 'HH24:MI:SS')   
--	     end as "DURAÇÃO"
--	    , case 
--	        when ("INÍCIO DO INTERVALO" is null or "FIM DO INTERVALO" is null) 
--	            then TO_CHAR((("end_of_operation" - "INÍCIO DA OPERAÇÃO")|| 'hour')::interval, 'HH24:MI:SS') 
--	        else TO_CHAR((("end_of_operation" - "FIM DO INTERVALO" + ("INÍCIO DO INTERVALO" - "INÍCIO DA OPERAÇÃO"))|| 'hour')::interval, 'HH24:MI:SS')   
--	     end as "DURAÇÃO_trad"
--	FROM tab_op 
--)
--SELECT 
--	"INÍCIO DA OPERAÇÃO"
--	, "INÍCIO DO INTERVALO"
--	, "FIM DO INTERVALO" 
--	, CASE 
--		WHEN "DURAÇÃO" < "DURAÇÃO_trad" THEN "FIM DA OPERAÇÃO"
--		ELSE end_of_operation
--	END as "FIM DA OPERAÇÃO"
--	, "ULTIMO EMPILHAMENTO"
--	, CASE 
--		WHEN "DURAÇÃO" < "DURAÇÃO_trad" THEN "DURAÇÃO"
--		ELSE "DURAÇÃO_trad"
--	END as "DURAÇÃO"
--	, to_char("INÍCIO DA OPERAÇÃO", 'YYYY-MM-DD') AS data_operacao
--FROM tab_calc
--
-- ############################# tabela tab_horas_trabalhadas.csv
--SELECT 
--    locality_name
--    , start_of_operation
--    , to_char(start_of_operation, 'YYYY-MM-DD') AS data_operacao
--    , assembler_name 
--    , max(end_assembly::timestamp) as fim
--    , min(start_assembly::timestamp) as inicio 
--    , max(end_assembly::timestamp) - min(start_assembly::timestamp) AS horas
--FROM tab_orders
--WHERE
--    pallet_type_name <> 'COMPLETO'
--    AND assembler_name IS NOT NULL
--GROUP BY
--    locality_name, start_of_operation, assembler_name  
--    

