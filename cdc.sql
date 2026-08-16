WITH tab_loads AS (
WITH loads_table AS (
	SELECT 
	    L.id AS load_id
	    , (
	    	SELECT	
	    		c."name" 
	    	FROM casadiconti.load_products lp
	    	INNER JOIN casadiconti.clients c ON (lp.client_id = c.id)
	    	WHERE 
	    		lp.load_id = L.id
	    	LIMIT 1
	    ) AS client_name		
	    , L.integration_id AS integration_id
	    , L.code AS load_code
	    , L.delivery_date AS delivery_date
	    , LC."name" AS locality_name
	    , V."name" AS vehicle_name
	    , L.dock AS dock
	    , L.assembled_percentage AS assembled_percentage
	    , L.checked_percentage AS checked_percentage
		, L.loaded_percentage AS loaded_percentage
	    , (
		    SELECT  
			    S."name" 
		    FROM casadiconti.load_histories LH  
		    INNER JOIN casadiconti.load_steps LS ON (LS.id = L.load_step_id)
		    INNER JOIN casadiconti.statuses S ON (S.id = LS.status_id)
		    WHERE 
			    LH.load_id = L.id 
		    ORDER BY 
			    LH.created_at DESC
		    LIMIT 1 
	    ) AS load_status_name
	    , L.weight AS load_weight
		, (
		 	SELECT 
			VT.weight_capacity 
			FROM casadiconti.vehicles V  
			INNER JOIN casadiconti.vehicle_types VT ON (V.vehicle_type_id  = VT.id)
			WHERE 
				L.vehicle_id = V.id
			LIMIT 1
		) AS vehicle_weight_capacity	
	    , (
		    SELECT 
			    ROUND((L.weight/VT.weight_capacity)*100)
			FROM casadiconti.vehicles V  
			INNER JOIN casadiconti.vehicle_types VT ON (V.vehicle_type_id  = VT.id)
			WHERE 
				L.vehicle_id = V.id
			LIMIT 1
		) AS vehicle_weight_occupation
		, (
			SELECT 
				sum(quantity)
			FROM casadiconti.order_products op
			LEFT JOIN casadiconti.products p ON (p.id = op.product_id)
			LEFT JOIN casadiconti.orders o ON (o.id = op.order_id)
			INNER JOIN casadiconti.fragilities f ON (f.id = p.fragility_id)
			WHERE 
				O.load_id = L.id
				AND f."name" IN ('RETORNAVEL CRITICO', 'RETORNAVEL')
			LIMIT 1
		) AS returnable_quantity_boxes
		, (
			SELECT 
				sum(quantity)
			FROM casadiconti.order_products op
			LEFT JOIN casadiconti.products p ON (p.id = op.product_id)
			LEFT JOIN casadiconti.orders o ON (o.id = op.order_id)
			INNER JOIN casadiconti.fragilities f ON (f.id = p.fragility_id)
			WHERE 
				O.load_id = L.id
				AND f."name" NOT IN ('RETORNAVEL CRITICO', 'RETORNAVEL')
			LIMIT 1
		) AS mix_quantity_boxes 
		, L.quantity_boxes AS quantity_boxes
		, 0 AS returnable_assembler_quantity
		, 0 AS mix_assembler_quantity
		, (
	 		SELECT 
				U."name" 
			FROM casadiconti.order_histories OH  
			LEFT JOIN casadiconti.history_types HT ON (HT.id = OH.history_type_id)
			LEFT JOIN casadiconti.orders O ON (O.id = OH.order_id)
			LEFT JOIN casadiconti.order_steps OS ON (OS.id = OH.order_step_id)
			LEFT JOIN casadiconti.statuses S ON (S.id = OS.status_id)
			LEFT JOIN casadiconti.users U ON (U.id = OH.user_id)
			WHERE 
				S."name" = 'Conferência'
				AND O.load_id = L.id  
			ORDER BY 
				OH.created_at DESC 
			LIMIT 1 		
		) AS checker	
		--, checking time
		, ( 
			ROUND(CAST((EXTRACT(EPOCH FROM(
			(
				SELECT 
					TO_CHAR(OH.created_at - INTERVAL '3 hour', 'YYYY-MM-DD HH24:MI:SS')::timestamp 
				FROM casadiconti.order_histories OH  
				LEFT JOIN casadiconti.history_types HT ON (HT.id = OH.history_type_id)
				LEFT JOIN casadiconti.orders O ON (O.id = OH.order_id)
				LEFT JOIN casadiconti.order_steps OS ON (OS.id = OH.order_step_id)
				LEFT JOIN casadiconti.statuses S ON (S.id = OS.status_id)
				WHERE 	
					S."name"  = 'Conferência'
					AND L.id = O.load_id
					AND HT."name" = 'Fim da Conferência'
				ORDER BY 
					OH.created_at DESC 
				LIMIT 1
			) -
			(
				SELECT 
					TO_CHAR(OH.created_at - INTERVAL '3 hour', 'YYYY-MM-DD HH24:MI:SS')::timestamp 
				FROM casadiconti.order_histories OH  
				LEFT JOIN casadiconti.history_types HT ON (HT.id = OH.history_type_id)
				LEFT JOIN casadiconti.orders O ON (O.id = OH.order_id)
				LEFT JOIN casadiconti.order_steps OS ON (OS.id = OH.order_step_id)
				LEFT JOIN casadiconti.statuses S ON (S.id = OS.status_id)
				WHERE 	
					S."name"  = 'Conferência'
					AND L.id = O.load_id
					AND HT."name" = 'Início da Conferência'
				ORDER BY 
					OH.created_at ASC  
				LIMIT 1
			)
			))) AS numeric)/60, 2)
		) AS checking_time -- tempo de conferencia em minutos	
		-- checker_under_count_error_quantity
		, (
			SELECT 
				SUM(CASE 
						WHEN ET."name" = 'CONTAGEM A MENOS' THEN 1
						ELSE 0
					END)
			FROM casadiconti.orders O
			LEFT JOIN casadiconti.blind_conference_errors BCE ON (BCE.order_id = O.id)
			LEFT JOIN casadiconti.error_types ET ON (ET.id = BCE.error_type_id)
			WHERE 
				O.load_id = L.id 
			GROUP BY 
				O.load_id
			LIMIT 1
		) AS checker_under_count_error_quantity
		-- checker_over_count_error_quantity
		, ( 
			SELECT 
				SUM(CASE 
						WHEN ET."name" = 'CONTAGEM A MAIS' THEN 1
						ELSE 0
					END)
			FROM casadiconti.orders O
			LEFT JOIN casadiconti.blind_conference_errors BCE ON (BCE.order_id = O.id)
			LEFT JOIN casadiconti.error_types ET ON (ET.id = BCE.error_type_id)
			WHERE 
				O.load_id = L.id 
			GROUP BY 
				O.load_id
			LIMIT 1		
		) AS checker_over_count_error_quantity
	    -- checker_total_error_quantity	
		, (
			SELECT
				SUM(CASE 
						WHEN ET."name" = 'CONTAGEM A MAIS' OR ET."name" = 'CONTAGEM A MENOS'THEN 1
						ELSE 0
					END)
			FROM casadiconti.orders O
			LEFT JOIN casadiconti.blind_conference_errors BCE ON (BCE.order_id = O.id)
			LEFT JOIN casadiconti.error_types ET ON (ET.id = BCE.error_type_id)
			WHERE 
				O.load_id = L.id 
			GROUP BY 
				O.load_id
			LIMIT 1
		) AS checker_total_error_quantity
		, NULL AS checker_2
		, NULL::FLOAT AS checking_time_2
		, NULL AS checker_2_under_count_error_quantity
		, NULL AS checker_2_over_count_error_quantity
		, NULL AS checker_2_total_error_quantity
		, NULL AS checker_3
		, NULL::FLOAT AS checking_time_3
		, NULL AS checker_3_under_count_error_quantity
		, NULL AS checker_3_over_count_error_quantity
		, NULL AS checker_3_total_error_quantity
		, (
			ROUND(CAST((EXTRACT(EPOCH FROM(
			(
			SELECT
				TO_CHAR(LH.created_at - INTERVAL '3 hour', 'YYYY-MM-DD HH24:MI:SS')::timestamp 
			FROM casadiconti.load_histories LH
			INNER JOIN casadiconti.history_types HT ON (HT.id = LH.history_type_id)
			WHERE
				HT."name" = 'Fim do Carregamento'
				AND LH.load_id = L.id
			ORDER BY
				LH.created_at
			LIMIT 1		
			) -
			(	
			SELECT
				TO_CHAR(LH.created_at - INTERVAL '3 hour', 'YYYY-MM-DD HH24:MI:SS')::timestamp 
			FROM casadiconti.load_histories LH
			INNER JOIN casadiconti.history_types HT ON (HT.id = LH.history_type_id)
			WHERE
				HT."name" = 'Início do Carregamento'
				AND LH.load_id = L.id
			ORDER BY
				LH.created_at
			LIMIT 1
			)
			))) AS numeric)/3600, 2)
		) AS loading_time -- tempo de carregamento em horas
		--, operation_time
		, ROUND((DO2.duration/3600.0), 2) AS operation_time
		, NOW() AS created_at
		, NOW() AS updated_at		
	FROM casadiconti.loads L
	LEFT JOIN casadiconti.localities LC ON (LC.id = L.locality_id)
	LEFT JOIN casadiconti.vehicles V ON (V.id = L.vehicle_id)
	LEFT JOIN casadiconti.daily_operations DO2 on (L.daily_operation_id = DO2.id)
	WHERE
	   L.delivery_date BETWEEN $1 AND $2
	   	AND L.assembled_percentage = 100
		AND L.checked_percentage = 100
		AND l.loaded_percentage = 100
)
SELECT
	*
	,(COALESCE(checking_time, 0) + COALESCE(checking_time_2, 0) + COALESCE(checking_time_3, 0)) AS checking_time_total
FROM loads_table
)
SELECT
	*
FROM tab_loads