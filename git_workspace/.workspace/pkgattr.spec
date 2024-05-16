<?xml version="1.0" encoding="utf-8"?>
<ATTRIBUTES format-rev="1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
	<ATTRIBUTE-DEFINITIONS>
		<DEFINITION format-rev="1" xsi:type="anAttributeDef">
			<NAME xsi:type="string">Estimated Duration [min]</NAME>
			<REQUIRED xsi:type="boolean">False</REQUIRED>
		</DEFINITION>
		<DEFINITION format-rev="2" xsi:type="anAttributeTreeValueDef">
			<NAME xsi:type="string">Execution Priority</NAME>
			<REQUIRED xsi:type="boolean">False</REQUIRED>
			<NODE-META-LIST-NON-LEAFS>
				<ELEMENT format-rev="1" xsi:type="anAttributeTreeNodeMetaEntryDef">
					<USE-AS-IDENTIFIER xsi:type="boolean">True</USE-AS-IDENTIFIER>
				</ELEMENT>
			</NODE-META-LIST-NON-LEAFS>
			<NODE-META-LIST-LEAFS>
				<ELEMENT format-rev="1" xsi:type="anAttributeTreeNodeMetaEntryDef">
					<USE-AS-IDENTIFIER xsi:type="boolean">True</USE-AS-IDENTIFIER>
				</ELEMENT>
			</NODE-META-LIST-LEAFS>
			<NODE-LIST>
				<ELEMENT format-rev="1" xsi:type="anTreeNodeDef">
					<VALUE-LIST>
						<VALUE xsi:type="string">1</VALUE>
					</VALUE-LIST>
				</ELEMENT>
				<ELEMENT format-rev="1" xsi:type="anTreeNodeDef">
					<VALUE-LIST>
						<VALUE xsi:type="string">2</VALUE>
					</VALUE-LIST>
				</ELEMENT>
				<ELEMENT format-rev="1" xsi:type="anTreeNodeDef">
					<VALUE-LIST>
						<VALUE xsi:type="string">3</VALUE>
					</VALUE-LIST>
				</ELEMENT>
				<ELEMENT format-rev="1" xsi:type="anTreeNodeDef">
					<VALUE-LIST>
						<VALUE xsi:type="string">4</VALUE>
					</VALUE-LIST>
				</ELEMENT>
				<ELEMENT format-rev="1" xsi:type="anTreeNodeDef">
					<VALUE-LIST>
						<VALUE xsi:type="string">5</VALUE>
					</VALUE-LIST>
				</ELEMENT>
			</NODE-LIST>
		</DEFINITION>
		<DEFINITION format-rev="2" xsi:type="anAttributeTreeValueDef">
			<NAME xsi:type="string">Status</NAME>
			<REQUIRED xsi:type="boolean">False</REQUIRED>
			<NODE-META-LIST-NON-LEAFS>
				<ELEMENT format-rev="1" xsi:type="anAttributeTreeNodeMetaEntryDef">
					<USE-AS-IDENTIFIER xsi:type="boolean">True</USE-AS-IDENTIFIER>
					<MAX-LENGTH-TREE xsi:type="integer">0</MAX-LENGTH-TREE>
				</ELEMENT>
				<ELEMENT format-rev="1" xsi:type="anAttributeTreeNodeMetaEntryDef"/>
			</NODE-META-LIST-NON-LEAFS>
			<NODE-META-LIST-LEAFS>
				<ELEMENT format-rev="1" xsi:type="anAttributeTreeNodeMetaEntryDef">
					<USE-AS-IDENTIFIER xsi:type="boolean">True</USE-AS-IDENTIFIER>
					<MAX-LENGTH-TREE xsi:type="integer">0</MAX-LENGTH-TREE>
				</ELEMENT>
				<ELEMENT format-rev="1" xsi:type="anAttributeTreeNodeMetaEntryDef"/>
			</NODE-META-LIST-LEAFS>
			<NODE-LIST>
				<ELEMENT format-rev="1" xsi:type="anTreeNodeDef">
					<VALUE-LIST>
						<VALUE xsi:type="string">ID_STATUS_001</VALUE>
						<VALUE xsi:type="string">Design</VALUE>
					</VALUE-LIST>
				</ELEMENT>
				<ELEMENT format-rev="1" xsi:type="anTreeNodeDef">
					<VALUE-LIST>
						<VALUE xsi:type="string">ID_STATUS_002</VALUE>
						<VALUE xsi:type="string">For Review</VALUE>
					</VALUE-LIST>
				</ELEMENT>
				<ELEMENT format-rev="1" xsi:type="anTreeNodeDef">
					<VALUE-LIST>
						<VALUE xsi:type="string">ID_STATUS_003</VALUE>
						<VALUE xsi:type="string">Locked</VALUE>
					</VALUE-LIST>
				</ELEMENT>
				<ELEMENT format-rev="1" xsi:type="anTreeNodeDef">
					<VALUE-LIST>
						<VALUE xsi:type="string">ID_STATUS_004</VALUE>
						<VALUE xsi:type="string">Ready</VALUE>
					</VALUE-LIST>
				</ELEMENT>
			</NODE-LIST>
		</DEFINITION>
		<DEFINITION format-rev="2" xsi:type="anAttributeTreeValueDef">
			<NAME xsi:type="string">Testlevel</NAME>
			<REQUIRED xsi:type="boolean">False</REQUIRED>
			<IS-MULTI-CHOICE xsi:type="boolean">True</IS-MULTI-CHOICE>
			<NODE-META-LIST-NON-LEAFS>
				<ELEMENT format-rev="1" xsi:type="anAttributeTreeNodeMetaEntryDef">
					<USE-AS-IDENTIFIER xsi:type="boolean">True</USE-AS-IDENTIFIER>
				</ELEMENT>
			</NODE-META-LIST-NON-LEAFS>
			<NODE-META-LIST-LEAFS>
				<ELEMENT format-rev="1" xsi:type="anAttributeTreeNodeMetaEntryDef">
					<USE-AS-IDENTIFIER xsi:type="boolean">True</USE-AS-IDENTIFIER>
				</ELEMENT>
			</NODE-META-LIST-LEAFS>
			<NODE-LIST>
				<ELEMENT format-rev="1" xsi:type="anTreeNodeDef">
					<VALUE-LIST>
						<VALUE xsi:type="string">component</VALUE>
					</VALUE-LIST>
				</ELEMENT>
				<ELEMENT format-rev="1" xsi:type="anTreeNodeDef">
					<VALUE-LIST>
						<VALUE xsi:type="string">module</VALUE>
					</VALUE-LIST>
				</ELEMENT>
				<ELEMENT format-rev="1" xsi:type="anTreeNodeDef">
					<VALUE-LIST>
						<VALUE xsi:type="string">not specified</VALUE>
					</VALUE-LIST>
				</ELEMENT>
				<ELEMENT format-rev="1" xsi:type="anTreeNodeDef">
					<VALUE-LIST>
						<VALUE xsi:type="string">subsystem</VALUE>
					</VALUE-LIST>
				</ELEMENT>
				<ELEMENT format-rev="1" xsi:type="anTreeNodeDef">
					<VALUE-LIST>
						<VALUE xsi:type="string">system</VALUE>
					</VALUE-LIST>
				</ELEMENT>
			</NODE-LIST>
		</DEFINITION>
        <DEFINITION format-rev="2" xsi:type="anAttributeTreeValueDef">
			<NAME xsi:type="string">Testplatform</NAME>
			<REQUIRED xsi:type="boolean">False</REQUIRED>
			<IS-MULTI-CHOICE xsi:type="boolean">True</IS-MULTI-CHOICE>
			<NODE-META-LIST-NON-LEAFS>
				<ELEMENT format-rev="1" xsi:type="anAttributeTreeNodeMetaEntryDef">
					<USE-AS-IDENTIFIER xsi:type="boolean">True</USE-AS-IDENTIFIER>
					<MAX-LENGTH-TREE xsi:type="integer">0</MAX-LENGTH-TREE>
				</ELEMENT>
				<ELEMENT format-rev="1" xsi:type="anAttributeTreeNodeMetaEntryDef"/>
			</NODE-META-LIST-NON-LEAFS>
			<NODE-META-LIST-LEAFS>
				<ELEMENT format-rev="1" xsi:type="anAttributeTreeNodeMetaEntryDef">
					<USE-AS-IDENTIFIER xsi:type="boolean">True</USE-AS-IDENTIFIER>
					<MAX-LENGTH-TREE xsi:type="integer">0</MAX-LENGTH-TREE>
				</ELEMENT>
				<ELEMENT format-rev="1" xsi:type="anAttributeTreeNodeMetaEntryDef"/>
			</NODE-META-LIST-LEAFS>
			<NODE-LIST>
				<ELEMENT format-rev="1" xsi:type="anTreeNodeDef">
					<VALUE-LIST>
						<VALUE xsi:type="string">ID_PLATFORM_001</VALUE>
                        <VALUE xsi:type="string">HiL</VALUE>
					</VALUE-LIST>
					<CHILD-LIST>
                        <ELEMENT format-rev="1" xsi:type="anTreeNodeDef">
                            <VALUE-LIST>
						        <VALUE xsi:type="string">ID_PLATFORM_002</VALUE>
                                <VALUE xsi:type="string">Component HiL</VALUE>
                            </VALUE-LIST>
                        </ELEMENT>
                        <ELEMENT format-rev="1" xsi:type="anTreeNodeDef">
                            <VALUE-LIST>
						        <VALUE xsi:type="string">ID_PLATFORM_003</VALUE>
                                <VALUE xsi:type="string">Integration HiL</VALUE>
                            </VALUE-LIST>
                        </ELEMENT>
                    </CHILD-LIST>
				</ELEMENT>
                <ELEMENT format-rev="1" xsi:type="anTreeNodeDef">
					<VALUE-LIST>
						<VALUE xsi:type="string">ID_PLATFORM_004</VALUE>
						<VALUE xsi:type="string">SiL</VALUE>
					</VALUE-LIST>
				</ELEMENT>
                <ELEMENT format-rev="1" xsi:type="anTreeNodeDef">
					<VALUE-LIST>
						<VALUE xsi:type="string">ID_PLATFORM_005</VALUE>
						<VALUE xsi:type="string">MiL</VALUE>
					</VALUE-LIST>
				</ELEMENT>
			</NODE-LIST>
		</DEFINITION>
		<DEFINITION format-rev="1" xsi:type="anAttributeDef">
			<NAME xsi:type="string">Designer</NAME>
			<REQUIRED xsi:type="boolean">False</REQUIRED>
		</DEFINITION>
		<DEFINITION format-rev="1" xsi:type="anAttributeDef">
			<NAME xsi:type="string">Design Contact</NAME>
			<REQUIRED xsi:type="boolean">False</REQUIRED>
		</DEFINITION>
		<DEFINITION format-rev="1" xsi:type="anAttributeDef">
			<NAME xsi:type="string">Design Department</NAME>
			<REQUIRED xsi:type="boolean">False</REQUIRED>
		</DEFINITION>
		<DEFINITION format-rev="1" xsi:type="anAttributeDef">
			<NAME xsi:type="string">Test Comment</NAME>
			<REQUIRED xsi:type="boolean">False</REQUIRED>
		</DEFINITION>
		<DEFINITION format-rev="1" xsi:type="anAttributeDef">
			<NAME xsi:type="string">Tools</NAME>
			<REQUIRED xsi:type="boolean">False</REQUIRED>
		</DEFINITION>
		<DEFINITION format-rev="1" xsi:type="anAttributeDef">
			<NAME xsi:type="string">VersionCounter</NAME>
			<REQUIRED xsi:type="boolean">False</REQUIRED>
		</DEFINITION>
	</ATTRIBUTE-DEFINITIONS>
</ATTRIBUTES>
