*** Keywords ***
Tabs
	FOR	${a}	IN	1
		IF	$a
			FOR	${b}	IN	1
				IF	$b
					Log	tabs
				END
			END
		END
	END

Mixed Separators
  FOR  ${a}  IN  1
   IF  $a
          FOR    ${b}    IN    1
	IF	$b
 Log  mixed
	END
          END
   END
  END
